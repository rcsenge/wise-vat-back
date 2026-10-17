"""Invoice processing flow. Orchestrates validation, VIES, matching, and rules."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session, col, select

from app.config import settings
from app.domain import vat_rules
from app.domain.claim_deadline import claim_deadline, expiry_reason, is_expired
from app.integrations.vies import validate_vat_number
from app.models.invoice_document import InvoiceDocument
from app.models.invoice_record import InvoiceRecord
from app.models.transaction import Transaction
from app.schemas.invoice import ExtractedInvoice
from app.schemas.invoice_flow import (
    ClaimPeriod,
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
MAX_CLAIM_RESULTS = 500
CLAIM_BATCH_SIZE = 500
# A card payment and its invoice date differ by a few days, for example at a hotel checkout.
MATCH_WINDOW_DAYS = 14
MAX_MATCH_CANDIDATES = 100
DEFAULT_RECEIPT_LIMIT = 50


def reference_date() -> date:
    """Return the date that the claim deadline check uses as today."""
    return settings.claim_reference_date or datetime.now(timezone.utc).date()


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

    if is_expired(invoice.issue_date, reference_date()):
        return InvoiceResult(
            status="rejected",
            invoice_number=invoice.invoice_number,
            reasons=[expiry_reason(invoice.issue_date)],
        )

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
        decision = vat_rules.evaluate_line(transaction.country, line.category, index, line.vat_amount, invoice.currency)
        outcomes.append(
            LineOutcome(
                line_index=decision.line_index,
                description=line.description,
                category=decision.category,
                eligible=decision.eligible,
                refundable_vat=decision.refundable_vat.amount,
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


@dataclass(frozen=True)
class OriginalDocument:
    """The uploaded PDF or photo. The claim package attaches it as the invoice copy."""

    filename: str
    media_type: str
    content: bytes


def submit_invoice(
    session: Session, submission: InvoiceSubmission, document: OriginalDocument | None = None
) -> InvoiceResult:
    """Run the full flow for one invoice. Store the result and the document. Return the result."""
    result = process_invoice(session, submission)
    refundable = sum((total.refundable_vat_total for total in result.country_totals), Decimal("0"))
    matched = result.matched_transaction
    record = InvoiceRecord(
        status=result.status,
        invoice_number=result.invoice_number,
        issue_date=submission.issue_date,
        merchant=submission.supplier.name,
        currency=submission.currency,
        gross_amount=submission.totals.gross_amount,
        refundable_vat=refundable,
        country=matched.country if matched else None,
        transaction_id=matched.transaction_id if matched else None,
        image_data_url=submission.image_data_url,
        result_json=result.model_dump_json(),
        invoice_json=submission.model_dump_json(by_alias=True, exclude={"image_data_url"}),
    )
    session.add(record)
    session.flush()
    if document is not None:
        session.add(
            InvoiceDocument(
                record_id=record.id,
                filename=document.filename,
                media_type=document.media_type,
                content=document.content,
            )
        )
    session.commit()
    return result


def list_receipts(session: Session, limit: int = DEFAULT_RECEIPT_LIMIT) -> list[ReceiptView]:
    """Return the stored invoices in the frontend receipt shape, newest first."""
    query = select(InvoiceRecord).order_by(col(InvoiceRecord.id).desc()).limit(limit)
    today = reference_date()
    return [_receipt_view(record, today) for record in session.exec(query).all()]


def _add_country_total(totals: dict[tuple[str, str], CountryTotal], country_total: CountryTotal) -> None:
    key = (country_total.country, country_total.currency)
    current = totals.get(key)
    if current is None:
        totals[key] = country_total
        return
    totals[key] = CountryTotal(
        country=current.country,
        currency=current.currency,
        refundable_vat_total=(current.refundable_vat_total + country_total.refundable_vat_total).quantize(_CENT),
        eligible_line_count=current.eligible_line_count + country_total.eligible_line_count,
        transaction_ids=current.transaction_ids + country_total.transaction_ids,
    )


def _is_record_expired(issue_date: date | None, today: date) -> bool:
    # A record from before the issue date column has no date. It stays claimable.
    return issue_date is not None and is_expired(issue_date, today)


def compute_claims(session: Session) -> ClaimsSummary:
    """Sum the approved invoices per country and currency. Split them by the claim deadline."""
    today = reference_date()
    approved = (
        select(InvoiceRecord.result_json, InvoiceRecord.issue_date)
        .where(InvoiceRecord.status == "approved")
        .order_by(col(InvoiceRecord.id))
        .execution_options(yield_per=CLAIM_BATCH_SIZE)
    )
    totals: dict[tuple[str, str], CountryTotal] = {}
    expired_totals: dict[tuple[str, str], CountryTotal] = {}
    # One refund period per country, currency and invoice year. Each period has its own deadline.
    period_totals: dict[tuple[str, str, int], tuple[Decimal, int]] = {}
    for result_json, issue_date in session.exec(approved):
        expired = _is_record_expired(issue_date, today)
        for country_total in InvoiceResult.model_validate_json(result_json).country_totals:
            _add_country_total(expired_totals if expired else totals, country_total)
            if issue_date is not None and not expired:
                key = (country_total.country, country_total.currency, issue_date.year)
                amount, count = period_totals.get(key, (Decimal("0"), 0))
                period_totals[key] = (amount + country_total.refundable_vat_total, count + 1)
    periods = sorted(
        (
            ClaimPeriod(
                country=country,
                currency=currency,
                year=year,
                period_start=date(year, 1, 1),
                claim_deadline=claim_deadline(date(year, 1, 1)),
                refundable_vat_total=amount.quantize(_CENT),
                invoice_count=count,
            )
            for (country, currency, year), (amount, count) in period_totals.items()
        ),
        key=lambda period: (period.claim_deadline, period.country),
    )
    newest = select(InvoiceRecord.result_json).order_by(col(InvoiceRecord.id).desc()).limit(MAX_CLAIM_RESULTS)
    results = [InvoiceResult.model_validate_json(result_json) for result_json in reversed(session.exec(newest).all())]
    return ClaimsSummary(
        per_country=list(totals.values()),
        expired_per_country=list(expired_totals.values()),
        periods=periods,
        reference_date=today,
        results=results,
    )


def _receipt_view(record: InvoiceRecord, today: date) -> ReceiptView:
    # SQLite returns a naive datetime. The stored value is UTC.
    created_at = record.created_at.replace(tzinfo=timezone.utc)
    result = InvoiceResult.model_validate_json(record.result_json)
    expired = result.status == "approved" and _is_record_expired(record.issue_date, today)
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
        reasons=[expiry_reason(record.issue_date)] if expired else result.reasons,
        issue_date=record.issue_date,
        claim_deadline=claim_deadline(record.issue_date) if record.issue_date else None,
        expired=expired,
    )
