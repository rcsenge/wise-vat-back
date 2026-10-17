"""Invoice processing flow. Orchestrates validation, VIES, matching, and rules."""
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session, col, select

from app.domain import vat_rules
from app.integrations.vies import validate_vat_number
from app.models.invoice_record import InvoiceRecord
from app.models.transaction import Transaction
from app.schemas.invoice import ExtractedInvoice
from app.schemas.invoice_flow import (
    ClaimsSummary,
    CountryTotal,
    InvoiceResult,
    InvoiceSubmission,
    LineOutcome,
    MatchedTransaction,
    ReceiptView,
)

BACKEND = Path(__file__).resolve().parents[2]
INVOICES_DIR = BACKEND / "seed" / "invoices"

_CENT = Decimal("0.01")
MAX_CLAIM_RECORDS = 500
# A card payment and its invoice date differ by a few days, for example at a hotel checkout.
MATCH_WINDOW_DAYS = 14
MAX_MATCH_CANDIDATES = 100
DEFAULT_RECEIPT_LIMIT = 50


def validate_invoice(invoice: ExtractedInvoice) -> list[str]:
    """Return the human-readable reasons why the invoice must be rejected."""
    reasons: list[str] = []
    if not invoice.issue_date:
        reasons.append("The invoice has no issue date.")
    if not invoice.supplier.name:
        reasons.append("The invoice has no supplier name.")
    if not invoice.supplier.vat_number:
        reasons.append("The invoice has no supplier VAT number.")
    if not invoice.supplier.address or not invoice.supplier.address.country_code:
        reasons.append("The invoice has no supplier country.")
    if not invoice.lines:
        reasons.append("The invoice has no lines.")
    return reasons


def find_transaction(session: Session, invoice: ExtractedInvoice) -> Transaction | None:
    """Return the unclaimed card transaction that matches the invoice.

    The transaction has the same gross total, currency and country. Its date is in the match window.
    The transaction with the date closest to the issue date wins.
    """
    gross = invoice.totals.gross_amount.quantize(_CENT)
    issued_at = datetime.combine(invoice.issue_date, time(hour=12), tzinfo=timezone.utc)
    window = timedelta(days=MATCH_WINDOW_DAYS)
    claimed = select(InvoiceRecord.transaction_id).where(InvoiceRecord.status == "approved")
    candidates = (
        select(Transaction)
        .where(
            Transaction.currency == invoice.currency,
            Transaction.country == invoice.supplier.address.country_code,
            Transaction.amount >= gross - _CENT,
            Transaction.amount <= gross + _CENT,
            Transaction.created_at >= issued_at - window,
            Transaction.created_at <= issued_at + window,
            col(Transaction.id).not_in(claimed),
        )
        .limit(MAX_MATCH_CANDIDATES)
    )
    matches = [
        transaction
        for transaction in session.exec(candidates).all()
        if Decimal(str(transaction.amount)).quantize(_CENT) == gross
    ]
    return min(matches, key=lambda transaction: abs(transaction.created_at - issued_at), default=None)


def process_invoice(session: Session, invoice: ExtractedInvoice) -> InvoiceResult:
    """Run the full flow for one invoice. Return the result."""
    reasons = validate_invoice(invoice)
    if reasons:
        return InvoiceResult(status="rejected", invoice_number=invoice.invoice_number, reasons=reasons)

    if not validate_vat_number(invoice.supplier.vat_number):
        return InvoiceResult(
            status="rejected",
            invoice_number=invoice.invoice_number,
            reasons=[f"The supplier VAT number {invoice.supplier.vat_number} is not valid."],
        )

    transaction = find_transaction(session, invoice)
    if transaction is None:
        return InvoiceResult(
            status="rejected",
            invoice_number=invoice.invoice_number,
            reasons=["No matching unclaimed card transaction found for the invoice total, country and date."],
        )

    if not vat_rules.is_supported(transaction.country):
        return InvoiceResult(
            status="rejected",
            invoice_number=invoice.invoice_number,
            matched_transaction=_match(transaction),
            reasons=[f"VAT back is not supported in country {transaction.country}."],
        )

    outcomes = []
    for index, line in enumerate(invoice.lines):
        decision = vat_rules.evaluate_line(transaction.country, line.category, index, line.vat_amount)
        outcomes.append(
            LineOutcome(
                line_index=decision.line_index,
                description=line.description,
                category=decision.category,
                eligible=decision.eligible,
                refundable_vat=decision.refundable_vat,
                reason=decision.reason,
            )
        )

    eligible = [outcome for outcome in outcomes if outcome.eligible]
    total = sum((outcome.refundable_vat for outcome in eligible), Decimal("0"))
    country_total = CountryTotal(
        country=transaction.country,
        currency=invoice.currency,
        refundable_vat_total=total.quantize(_CENT),
        eligible_line_count=len(eligible),
        transaction_ids=[transaction.id],
    )

    if not eligible:
        return InvoiceResult(
            status="rejected",
            invoice_number=invoice.invoice_number,
            matched_transaction=_match(transaction),
            reasons=["No invoice line is eligible for VAT back."],
            line_outcomes=outcomes,
        )

    return InvoiceResult(
        status="approved",
        invoice_number=invoice.invoice_number,
        reasons=["The invoice is approved for VAT back."],
        matched_transaction=_match(transaction),
        line_outcomes=outcomes,
        country_totals=[country_total],
    )


def _match(transaction: Transaction) -> MatchedTransaction:
    return MatchedTransaction(
        transaction_id=transaction.id,
        amount=Decimal(str(transaction.amount)),
        currency=transaction.currency,
        country=transaction.country,
        merchant=transaction.merchant,
    )


def iter_seed_invoices(directory: Path = INVOICES_DIR) -> list[InvoiceSubmission]:
    """Load the hardcoded seed invoices from disk."""
    invoices: list[InvoiceSubmission] = []
    for path in sorted(directory.glob("*.json")):
        invoices.append(InvoiceSubmission.model_validate_json(path.read_text(encoding="utf-8")))
    return invoices


def submit_invoice(session: Session, submission: InvoiceSubmission) -> InvoiceResult:
    """Run the full flow for one invoice. Store the result. Return the result."""
    result = process_invoice(session, submission)
    refundable = sum((total.refundable_vat_total for total in result.country_totals), Decimal("0"))
    matched = result.matched_transaction
    record = InvoiceRecord(
        status=result.status,
        invoice_number=result.invoice_number,
        merchant=submission.supplier.name,
        currency=submission.currency,
        gross_amount=submission.totals.gross_amount,
        refundable_vat=refundable,
        country=matched.country if matched else None,
        transaction_id=matched.transaction_id if matched else None,
        image_data_url=submission.image_data_url,
        result_json=result.model_dump_json(),
    )
    session.add(record)
    session.commit()
    return result


def list_receipts(session: Session, limit: int = DEFAULT_RECEIPT_LIMIT) -> list[ReceiptView]:
    """Return the stored invoices in the frontend receipt shape, newest first."""
    query = select(InvoiceRecord).order_by(col(InvoiceRecord.id).desc()).limit(limit)
    return [_receipt_view(record) for record in session.exec(query).all()]


def compute_claims(session: Session) -> ClaimsSummary:
    """Sum the stored approved invoices per country and currency."""
    query = select(InvoiceRecord).order_by(col(InvoiceRecord.id)).limit(MAX_CLAIM_RECORDS)
    results = [InvoiceResult.model_validate_json(record.result_json) for record in session.exec(query).all()]
    totals: dict[tuple[str, str], CountryTotal] = {}
    for result in results:
        for country_total in result.country_totals:
            key = (country_total.country, country_total.currency)
            current = totals.get(key)
            if current is None:
                totals[key] = country_total
            else:
                totals[key] = CountryTotal(
                    country=current.country,
                    currency=current.currency,
                    refundable_vat_total=(current.refundable_vat_total + country_total.refundable_vat_total).quantize(_CENT),
                    eligible_line_count=current.eligible_line_count + country_total.eligible_line_count,
                    transaction_ids=current.transaction_ids + country_total.transaction_ids,
                )
    return ClaimsSummary(per_country=list(totals.values()), results=results)


def _receipt_view(record: InvoiceRecord) -> ReceiptView:
    # SQLite returns a naive datetime. The stored value is UTC.
    created_at = record.created_at.replace(tzinfo=timezone.utc)
    result = InvoiceResult.model_validate_json(record.result_json)
    return ReceiptView(
        id=str(record.id),
        merchant=record.merchant,
        amount=record.gross_amount.quantize(_CENT),
        tax_amount=record.refundable_vat.quantize(_CENT),
        currency=record.currency,
        country=record.country,
        scanned_at=int(created_at.timestamp() * 1000),
        image_data_url=record.image_data_url,
        status=result.status,
        reasons=result.reasons,
    )
