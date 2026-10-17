"""The claim package for one refund country and one refund period (a calendar year).

The combined package holds an overview and one such package per open refund period.

The accountant submits the refund application through the electronic portal of the
Member State of establishment (Directive 2008/9/EC, Art. 7). The package holds every
value that the application form asks for (Art. 8 and Art. 9), the invoice copies, the
card payments and the decision log. A ZIP file carries the package.
"""
import base64
import csv
import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import font_roboto
from fpdf import FPDF
from fpdf.fonts import FontFace
from sqlmodel import Session, col, select

from app.config import settings
from app.domain.claim_deadline import claim_deadline, is_expired
from app.integrations.rates_cache import cross_rate, load_rates_table
from app.models.invoice_document import InvoiceDocument
from app.models.invoice_record import InvoiceRecord
from app.models.transaction import Transaction
from app.schemas.invoice import ExpenseCategory, ExtractedInvoice
from app.schemas.invoice_flow import InvoiceResult
from app.services.invoice_flow import compute_claims, reference_date

MAX_PACKAGE_INVOICES = 1000
CENT = Decimal("0.01")
ANNUAL_MINIMUM_EUR = Decimal("50")  # Art. 17(2): the minimum for an application that covers a calendar year
COPY_LIMIT_EUR = Decimal("1000")  # Art. 10: the refund country can ask for a copy above this taxable amount
FUEL_COPY_LIMIT_EUR = Decimal("250")
URGENT_DAYS = 30

COUNTRY_NAMES = {
    "AT": "Austria",
    "CZ": "Czechia",
    "DE": "Germany",
    "DK": "Denmark",
    "FR": "France",
    "HU": "Hungary",
    "IT": "Italy",
    "NL": "the Netherlands",
    "PL": "Poland",
    "SE": "Sweden",
}

# Directive 2008/9/EC, Art. 9(1): the codes of the goods and services on the application.
CATEGORY_CODES = {category.value: index for index, category in enumerate(ExpenseCategory, start=1)}
CATEGORY_LABELS = {
    1: "Fuel",
    2: "Hiring of means of transport",
    3: "Other expenditure related to means of transport",
    4: "Road tolls and road user charge",
    5: "Travel expenses, such as taxi fares and public transport fares",
    6: "Accommodation",
    7: "Food, drink and restaurant services",
    8: "Admissions to fairs and exhibitions",
    9: "Expenditure on luxuries, amusements and entertainment",
    10: "Other",
}
MEDIA_EXTENSIONS = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}
FONT_DIRECTORY = Path(font_roboto.__file__).parent / "files"


class PackageError(Exception):
    """The package cannot be built."""

    def __init__(self, status_code: int, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.status_code = status_code
        self.reasons = reasons


@dataclass(frozen=True)
class PackageLine:
    code: int
    category: str
    description: str
    net_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    deductible_vat: Decimal

    @property
    def deductible_share(self) -> Decimal:
        if self.vat_amount == 0:
            return Decimal("0")
        return (self.deductible_vat / self.vat_amount * 100).quantize(Decimal("1"))


@dataclass(frozen=True)
class PackageInvoice:
    row: int
    record: InvoiceRecord
    invoice: ExtractedInvoice
    result: InvoiceResult
    lines: list[PackageLine]
    transaction: Transaction | None
    copy_file: str | None
    copy_content: bytes | None
    copy_note: str
    copy_requirement: str  # "yes", "no" or "check"

    @property
    def deductible_vat(self) -> Decimal:
        return sum((line.deductible_vat for line in self.lines), Decimal("0")).quantize(CENT)


@dataclass(frozen=True)
class ClaimPackage:
    filename: str
    content: bytes


def _money(value: Decimal) -> str:
    return f"{value.quantize(CENT):,.2f}"


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")[:60] or "invoice"


def _country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code, code)


def _long_date(value: date) -> str:
    return f"{value.day} {value:%B %Y}"


def _copy_requirement(invoice: ExtractedInvoice) -> str:
    if invoice.currency != "EUR":
        return "check"
    is_fuel = any(line.category == ExpenseCategory.FUEL for line in invoice.lines)
    limit = FUEL_COPY_LIMIT_EUR if is_fuel else COPY_LIMIT_EUR
    return "yes" if invoice.totals.net_amount >= limit else "no"


def _invoice_copy(record: InvoiceRecord, document: InvoiceDocument | None, row: int, number: str) -> tuple[str | None, bytes | None, str]:
    base = f"02_invoice_copies/{row:03d}_{_safe_name(number)}"
    if document is not None:
        extension = MEDIA_EXTENSIONS.get(document.media_type, "bin")
        return f"{base}.{extension}", document.content, "Original upload"
    if record.image_data_url and record.image_data_url.startswith("data:image/jpeg;base64,"):
        preview = base64.b64decode(record.image_data_url.split(",", 1)[1])
        return f"{base}_preview.jpg", preview, "Preview image only. Attach the original invoice."
    return None, None, "No copy stored. The invoice came as data. Attach the original invoice."


def _package_lines(invoice: ExtractedInvoice, result: InvoiceResult) -> list[PackageLine]:
    deductible_by_index = {outcome.line_index: outcome.refundable_vat for outcome in result.line_outcomes}
    return [
        PackageLine(
            code=CATEGORY_CODES[line.category.value],
            category=line.category.value,
            description=line.description,
            net_amount=line.net_amount,
            vat_rate=line.vat_rate,
            vat_amount=line.vat_amount,
            deductible_vat=deductible_by_index.get(index, Decimal("0")).quantize(CENT),
        )
        for index, line in enumerate(invoice.lines)
    ]


def load_package_invoices(session: Session, country: str, year: int) -> list[PackageInvoice]:
    """Return the approved invoices of the country and the year, oldest first."""
    query = (
        select(InvoiceRecord)
        .where(
            InvoiceRecord.status == "approved",
            InvoiceRecord.country == country,
            col(InvoiceRecord.issue_date) >= date(year, 1, 1),
            col(InvoiceRecord.issue_date) <= date(year, 12, 31),
            col(InvoiceRecord.invoice_json).is_not(None),
        )
        .order_by(col(InvoiceRecord.issue_date), col(InvoiceRecord.id))
        .limit(MAX_PACKAGE_INVOICES + 1)
    )
    records = session.exec(query).all()
    if len(records) > MAX_PACKAGE_INVOICES:
        raise PackageError(413, [f"The period has more than {MAX_PACKAGE_INVOICES} invoices. Split it into quarters."])
    invoices: list[PackageInvoice] = []
    for row, record in enumerate(records, start=1):
        invoice = ExtractedInvoice.model_validate_json(record.invoice_json)
        result = InvoiceResult.model_validate_json(record.result_json)
        document = session.exec(select(InvoiceDocument).where(InvoiceDocument.record_id == record.id)).first()
        transaction = session.get(Transaction, record.transaction_id) if record.transaction_id else None
        copy_file, copy_content, copy_note = _invoice_copy(record, document, row, invoice.invoice_number or f"row-{row}")
        invoices.append(
            PackageInvoice(
                row=row,
                record=record,
                invoice=invoice,
                result=result,
                lines=_package_lines(invoice, result),
                transaction=transaction,
                copy_file=copy_file,
                copy_content=copy_content,
                copy_note=copy_note,
                copy_requirement=_copy_requirement(invoice),
            )
        )
    return invoices


def _rows_phrase(rows: list[int], singular: str, plural: str) -> str:
    """Return "Row 3 has" or "Rows 1, 4 have" for the warning texts."""
    if len(rows) == 1:
        return f"Row {rows[0]} {singular}"
    return f"Rows {', '.join(map(str, rows))} {plural}"


def _warnings(invoices: list[PackageInvoice], currency: str, total: Decimal, deadline: date, today: date) -> list[str]:
    warnings: list[str] = []
    days_left = (deadline - today).days
    if days_left < 0:
        warnings.append(f"The deadline passed on {_long_date(deadline)}. The tax authority rejects a late application.")
    elif days_left <= URGENT_DAYS:
        warnings.append(f"Only {days_left} days are left until the deadline on {_long_date(deadline)}.")
    if currency == "EUR" and total < ANNUAL_MINIMUM_EUR:
        warnings.append(f"The total is below the EUR {ANNUAL_MINIMUM_EUR} minimum for an annual application (Art. 17).")
    if currency != "EUR":
        warnings.append(
            f"The amounts are in {currency}. The EUR 50 minimum and the EUR 1,000 copy limit apply as the {currency} equivalent."
        )
    missing = [invoice.row for invoice in invoices if invoice.copy_note != "Original upload"]
    if missing:
        warnings.append(f"{_rows_phrase(missing, 'has', 'have')} no original copy in the package. Attach the original invoice.")
    required = [invoice.row for invoice in invoices if invoice.copy_requirement == "yes"]
    if required:
        warnings.append(f"{_rows_phrase(required, 'reaches', 'reach')} the copy limit. Upload the copy with the application (Art. 10).")
    partial = sum(1 for invoice in invoices for line in invoice.lines if 0 < line.deductible_vat < line.vat_amount)
    if partial:
        lines_phrase = "1 line is" if partial == 1 else f"{partial} lines are"
        warnings.append(f"{lines_phrase} only partly refundable. The lines file shows the deductible VAT and the share.")
    return warnings


def _application_lines_csv(invoices: list[PackageInvoice]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow([
        "row", "invoice_number", "issue_date", "supplier_name", "supplier_vat_number", "supplier_street",
        "supplier_postal_code", "supplier_city", "supplier_country", "goods_services_code", "goods_services",
        "description", "currency", "taxable_amount", "vat_rate_percent", "vat_amount", "deductible_vat",
        "deductible_share_percent", "invoice_copy_file", "copy_requested_by_refund_country",
    ])
    for item in invoices:
        address = item.invoice.supplier.address
        for line in item.lines:
            writer.writerow([
                item.row, item.invoice.invoice_number or "", item.invoice.issue_date.isoformat(), item.invoice.supplier.name,
                item.invoice.supplier.vat_number or "", address.street or "", address.postal_code or "", address.city or "",
                address.country_code, line.code, CATEGORY_LABELS[line.code], line.description, item.invoice.currency,
                f"{line.net_amount:.2f}", f"{line.vat_rate}", f"{line.vat_amount:.2f}", f"{line.deductible_vat:.2f}",
                f"{line.deductible_share}", item.copy_file or "", item.copy_requirement,
            ])
    # The byte order mark lets Excel read the accents correctly.
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def _transactions_csv(invoices: list[PackageInvoice]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(["row", "invoice_number", "transaction_id", "payment_date", "merchant", "amount", "currency", "country"])
    for item in invoices:
        payment = item.transaction
        writer.writerow([
            item.row, item.invoice.invoice_number or "", payment.id if payment else "",
            payment.created_at.date().isoformat() if payment else "", payment.merchant if payment else "",
            f"{Decimal(str(payment.amount)):.2f}" if payment else "", payment.currency if payment else "",
            payment.country if payment else "",
        ])
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def _decision_log_csv(invoices: list[PackageInvoice]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(["row", "invoice_number", "check", "result", "reason"])
    for item in invoices:
        number = item.invoice.invoice_number or ""
        writer.writerow([item.row, number, "required fields", "passed", "The invoice has every required field."])
        writer.writerow([item.row, number, "VIES", "passed", f"The supplier VAT number {item.invoice.supplier.vat_number} passed the VAT number check."])
        if item.transaction:
            writer.writerow([
                item.row, number, "card payment", "matched",
                f"Transaction {item.transaction.id}: {Decimal(str(item.transaction.amount)):.2f} {item.transaction.currency}.",
            ])
        for outcome in item.result.line_outcomes:
            writer.writerow([item.row, number, f"line {outcome.line_index + 1} rule", "eligible" if outcome.eligible else "not eligible", outcome.reason])
        writer.writerow([item.row, number, "decision", item.result.status, "; ".join(item.result.reasons)])
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def _application_json(invoices: list[PackageInvoice], country: str, year: int, currency: str, total: Decimal, deadline: date, generated_at: datetime) -> bytes:
    data = {
        "generator": "SIGINT",
        "generated_at": generated_at.isoformat(),
        "legal_basis": "Council Directive 2008/9/EC, Art. 8 and Art. 9",
        "applicant": {
            "name": settings.applicant_name,
            "vat_number": settings.applicant_vat_number,
            "address": settings.applicant_address,
            "email": settings.applicant_email,
            "iban": settings.applicant_iban,
            "bic": settings.applicant_bic,
            "business_activity": settings.applicant_activity,
            "member_state_of_establishment": settings.applicant_establishment_country,
        },
        "member_state_of_refund": country,
        "refund_period": {"start": date(year, 1, 1).isoformat(), "end": date(year, 12, 31).isoformat()},
        "claim_deadline": deadline.isoformat(),
        "currency": currency,
        "deductible_vat_total": f"{total:.2f}",
        "invoices": [
            {
                "row": item.row,
                "invoice_number": item.invoice.invoice_number,
                "issue_date": item.invoice.issue_date.isoformat(),
                "supplier": item.invoice.supplier.model_dump(mode="json", by_alias=True),
                "currency": item.invoice.currency,
                "taxable_amount": f"{item.invoice.totals.net_amount:.2f}",
                "vat_amount": f"{item.invoice.totals.vat_amount:.2f}",
                "deductible_vat": f"{item.deductible_vat:.2f}",
                "lines": [
                    {
                        "goods_services_code": line.code,
                        "category": line.category,
                        "description": line.description,
                        "taxable_amount": f"{line.net_amount:.2f}",
                        "vat_rate_percent": str(line.vat_rate),
                        "vat_amount": f"{line.vat_amount:.2f}",
                        "deductible_vat": f"{line.deductible_vat:.2f}",
                        "deductible_share_percent": str(line.deductible_share),
                    }
                    for line in item.lines
                ],
                "card_transaction_id": item.transaction.id if item.transaction else None,
                "invoice_copy_file": item.copy_file,
            }
            for item in invoices
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


class _SummaryPdf(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Roboto", size=7)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, f"SIGINT claim package · page {self.page_no()}/{{nb}}", align="C")


def _summary_pdf(invoices: list[PackageInvoice], country: str, year: int, currency: str, total: Decimal, deadline: date, today: date, warnings: list[str], generated_at: datetime) -> bytes:
    pdf = _SummaryPdf(format="A4")
    pdf.add_font("Roboto", "", str(FONT_DIRECTORY / "Roboto-Regular.ttf"))
    pdf.add_font("Roboto", "B", str(FONT_DIRECTORY / "Roboto-Bold.ttf"))
    pdf.set_margins(16, 16, 16)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    width = pdf.epw

    pdf.set_font("Roboto", "B", 18)
    pdf.cell(0, 9, "VAT refund application package", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", size=10)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(
        0, 6,
        f"Member State of refund: {_country_name(country)} ({country}) · Refund period: 1 January {year} – 31 December {year}",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.cell(0, 6, f"Generated on {_long_date(generated_at.date())} for the accountant of {settings.applicant_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # The key figures box.
    days_left = (deadline - today).days
    pdf.set_fill_color(226, 246, 213)
    pdf.set_font("Roboto", "B", 11)
    pdf.cell(width / 3, 7, "Deductible VAT to claim", fill=True)
    pdf.cell(width / 3, 7, "Invoices", fill=True)
    pdf.cell(width / 3, 7, "Claim deadline", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", "B", 16)
    pdf.cell(width / 3, 10, f"{_money(total)} {currency}", fill=True)
    pdf.cell(width / 3, 10, str(len(invoices)), fill=True)
    pdf.cell(width / 3, 10, _long_date(deadline), fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", size=9)
    status = "Deadline passed" if is_expired(date(year, 1, 1), today) else f"{days_left} days left"
    pdf.cell(width, 6, f"Status on {_long_date(today)}: {status}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def heading(text: str) -> None:
        pdf.set_font("Roboto", "B", 12)
        pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=9)

    def paragraph(text: str) -> None:
        pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")

    heading("Applicant")
    for label, value in (
        ("Name", settings.applicant_name),
        ("VAT number", settings.applicant_vat_number),
        ("Address", settings.applicant_address),
        ("E-mail", settings.applicant_email),
        ("Business activity", settings.applicant_activity),
        ("Bank account (IBAN / BIC)", f"{settings.applicant_iban} / {settings.applicant_bic}"),
    ):
        pdf.cell(48, 5, label)
        pdf.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    heading("How to submit")
    for number, step in enumerate((
        f"Log in to {settings.applicant_establishment_portal}. The portal forwards the application to {_country_name(country)}.",
        f"Start a new EU VAT refund application. Member State of refund: {country}. Period: 1 January {year} – 31 December {year}.",
        "Enter the applicant data above.",
        "Enter one invoice line per row of 01_refund_application_lines.csv. The file uses the goods and services codes of Art. 9.",
        "Attach the invoice copies from the 02_invoice_copies folder when the form or the refund country asks for them.",
        f"Submit before {_long_date(deadline)}. Keep 04_decision_log.csv for a later question from the tax authority.",
    ), start=1):
        paragraph(f"{number}. {step}")
    pdf.ln(2)

    if warnings:
        heading("Check before you submit")
        pdf.set_text_color(168, 32, 13)
        for warning in warnings:
            paragraph(f"• {warning}")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    heading("Invoices")
    pdf.set_font("Roboto", size=7.5)
    with pdf.table(
        col_widths=(7, 22, 30, 46, 26, 12, 22, 22, 22),
        text_align=("RIGHT", "LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "RIGHT", "RIGHT", "RIGHT"),
        line_height=4.2,
        headings_style=FontFace(emphasis="BOLD", fill_color=(226, 246, 213)),
    ) as table:
        header = table.row()
        for title in ("#", "Date", "Invoice no.", "Supplier", "Supplier VAT no.", "Codes", "Taxable", "VAT", "Deductible"):
            header.cell(title)
        for item in invoices:
            row = table.row()
            row.cell(str(item.row))
            row.cell(item.invoice.issue_date.isoformat())
            row.cell(item.invoice.invoice_number or "-")
            row.cell(item.invoice.supplier.name)
            row.cell(item.invoice.supplier.vat_number or "-")
            row.cell(", ".join(sorted({str(line.code) for line in item.lines}, key=int)))
            row.cell(_money(item.invoice.totals.net_amount))
            row.cell(_money(item.invoice.totals.vat_amount))
            row.cell(_money(item.deductible_vat))
    pdf.set_font("Roboto", size=9)
    pdf.ln(3)

    heading("Files in this package")
    for name, text in (
        ("00_summary.pdf", "This summary."),
        ("01_refund_application_lines.csv", "One row per invoice line with every field of the application form (Art. 8 and 9). Excel opens it."),
        ("02_invoice_copies/", "The invoice copies, named by row number."),
        ("03_card_transactions.csv", "The card payments that match the invoices."),
        ("04_decision_log.csv", "Why each invoice is claimable: required fields, VIES, card payment, country rules."),
        ("05_application_data.json", "The same data for software import."),
    ):
        pdf.set_font("Roboto", "B", 9)
        pdf.cell(62, 5, name)
        pdf.set_font("Roboto", size=9)
        pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_text_color(110, 110, 110)
    pdf.set_font("Roboto", size=7.5)
    paragraph(
        "SIGINT prepares the data from the invoices and the card payments. The applicant stays responsible for the application. "
        "Check the values against the original invoices before you submit."
    )
    return bytes(pdf.output())


@dataclass(frozen=True)
class PeriodPackage:
    """The files of one refund application and the key figures for the overview."""

    country: str
    year: int
    currency: str
    total: Decimal
    invoice_count: int
    deadline: date
    warnings: list[str]
    files: list[tuple[str, bytes]]


def build_period_package(session: Session, country: str, year: int, today: date, generated_at: datetime) -> PeriodPackage:
    """Build the files for the country and the year. Raise PackageError without approved invoices."""
    invoices = load_package_invoices(session, country, year)
    if not invoices:
        raise PackageError(404, [f"There are no approved invoices for {_country_name(country)} in {year}."])
    currencies = sorted({item.invoice.currency for item in invoices})
    if len(currencies) > 1:
        raise PackageError(409, [f"The invoices use more than one currency: {', '.join(currencies)}."])
    currency = currencies[0]
    deadline = claim_deadline(date(year, 1, 1))
    total = sum((item.deductible_vat for item in invoices), Decimal("0")).quantize(CENT)
    warnings = _warnings(invoices, currency, total, deadline, today)

    files = [
        ("00_summary.pdf", _summary_pdf(invoices, country, year, currency, total, deadline, today, warnings, generated_at)),
        ("01_refund_application_lines.csv", _application_lines_csv(invoices)),
        *[(item.copy_file, item.copy_content) for item in invoices if item.copy_file and item.copy_content],
        ("03_card_transactions.csv", _transactions_csv(invoices)),
        ("04_decision_log.csv", _decision_log_csv(invoices)),
        ("05_application_data.json", _application_json(invoices, country, year, currency, total, deadline, generated_at)),
    ]
    return PeriodPackage(country, year, currency, total, len(invoices), deadline, warnings, files)


def _zip(files: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files:
            archive.writestr(name, content)
    return buffer.getvalue()


def build_claim_package(session: Session, country: str, year: int) -> ClaimPackage:
    """Build the ZIP package for the country and the year. Raise PackageError without approved invoices."""
    package = build_period_package(session, country, year, reference_date(), datetime.now(timezone.utc))
    return ClaimPackage(filename=f"SIGINT-VAT-refund-{country}-{year}.zip", content=_zip(package.files))


def period_folder(package: PeriodPackage) -> str:
    return f"{package.country}_{package.year}"


def _to_eur(amount: Decimal, currency: str) -> Decimal | None:
    """Return the EUR equivalent at the demo rate. Return None for a currency without a rate."""
    try:
        return (amount * cross_rate(currency, "EUR")).quantize(CENT)
    except KeyError:
        return None


def _overview_pdf(packages: list[PeriodPackage], today: date, generated_at: datetime) -> bytes:
    pdf = _SummaryPdf(format="A4")
    pdf.add_font("Roboto", "", str(FONT_DIRECTORY / "Roboto-Regular.ttf"))
    pdf.add_font("Roboto", "B", str(FONT_DIRECTORY / "Roboto-Bold.ttf"))
    pdf.set_margins(16, 16, 16)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    width = pdf.epw

    eur_values = [_to_eur(package.total, package.currency) for package in packages]
    eur_total = sum((value for value in eur_values if value is not None), Decimal("0"))
    is_converted = any(package.currency != "EUR" for package in packages)
    invoice_count = sum(package.invoice_count for package in packages)
    first_deadline = min(package.deadline for package in packages)

    pdf.set_font("Roboto", "B", 18)
    pdf.cell(0, 9, "VAT refund packages: every country", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", size=10)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 6, f"Generated on {_long_date(generated_at.date())} for the accountant of {settings.applicant_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # The key figures box.
    pdf.set_fill_color(226, 246, 213)
    pdf.set_font("Roboto", "B", 11)
    for index, title in enumerate(("Deductible VAT to claim", "Invoices", "Applications", "First deadline")):
        pdf.cell(width / 4, 7, title, fill=True, **({"new_x": "LMARGIN", "new_y": "NEXT"} if index == 3 else {}))
    pdf.set_font("Roboto", "B", 13)
    pdf.cell(width / 4, 10, f"{'≈ ' if is_converted else ''}{_money(eur_total)} EUR", fill=True)
    pdf.cell(width / 4, 10, str(invoice_count), fill=True)
    pdf.cell(width / 4, 10, str(len(packages)), fill=True)
    pdf.cell(width / 4, 10, _long_date(first_deadline), fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Roboto", size=9)
    days_left = (first_deadline - today).days
    pdf.cell(width, 6, f"Status on {_long_date(today)}: {days_left} days left until the first deadline", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def heading(text: str) -> None:
        pdf.set_font("Roboto", "B", 12)
        pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=9)

    def paragraph(text: str) -> None:
        pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")

    heading("Applications")
    pdf.set_font("Roboto", size=8.5)
    with pdf.table(
        col_widths=(34, 14, 16, 30, 26, 32, 26),
        text_align=("LEFT", "LEFT", "RIGHT", "RIGHT", "RIGHT", "LEFT", "LEFT"),
        line_height=4.6,
        headings_style=FontFace(emphasis="BOLD", fill_color=(226, 246, 213)),
    ) as table:
        header = table.row()
        for title in ("Country of refund", "Period", "Invoices", "Deductible VAT", "≈ EUR", "Deadline", "Folder"):
            header.cell(title)
        for package, eur in zip(packages, eur_values):
            row = table.row()
            row.cell(f"{_country_name(package.country)} ({package.country})")
            row.cell(str(package.year))
            row.cell(str(package.invoice_count))
            row.cell(f"{_money(package.total)} {package.currency}")
            row.cell(_money(eur) if eur is not None else "-")
            row.cell(_long_date(package.deadline))
            row.cell(f"{period_folder(package)}/")
        total_row = table.row()
        total_row.cell("Total", style=FontFace(emphasis="BOLD"))
        total_row.cell("")
        total_row.cell(str(invoice_count), style=FontFace(emphasis="BOLD"))
        total_row.cell("")
        total_row.cell(_money(eur_total), style=FontFace(emphasis="BOLD"))
        total_row.cell("")
        total_row.cell("")
    pdf.set_font("Roboto", size=9)
    pdf.ln(3)

    heading("How to submit")
    for number, step in enumerate((
        "Submit one refund application per folder. Each folder holds the package of one country and one year.",
        "Open 00_summary.pdf in the folder first. It lists the applicant data, the steps and the checks for that country.",
        f"Submit every application through {settings.applicant_establishment_portal}.",
        f"Submit before the deadline of each row. The first deadline is {_long_date(first_deadline)}.",
    ), start=1):
        paragraph(f"{number}. {step}")
    pdf.ln(2)

    warnings = [
        f"{_country_name(package.country)[:1].upper()}{_country_name(package.country)[1:]} {package.year}: {warning}"
        for package in packages
        for warning in package.warnings
    ]
    if warnings:
        heading("Check before you submit")
        pdf.set_text_color(168, 32, 13)
        for warning in warnings:
            paragraph(f"• {warning}")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    pdf.set_text_color(110, 110, 110)
    pdf.set_font("Roboto", size=7.5)
    if is_converted:
        table_rates = load_rates_table()
        paragraph(
            f"The EUR values use the {table_rates.source} rates of {_long_date(table_rates.as_of)}. They show the size of the claims only. "
            "Each refund country pays in its own currency."
        )
    paragraph(
        "SIGINT prepares the data from the invoices and the card payments. The applicant stays responsible for the applications. "
        "Check the values against the original invoices before you submit."
    )
    return bytes(pdf.output())


def build_all_claims_package(session: Session) -> ClaimPackage:
    """Build one ZIP with an overview and one folder per open refund period. Raise PackageError without open periods."""
    periods = sorted({(period.country, period.year) for period in compute_claims(session).periods})
    if not periods:
        raise PackageError(404, ["There are no approved invoices with an open claim deadline."])
    today = reference_date()
    generated_at = datetime.now(timezone.utc)
    packages = [build_period_package(session, country, year, today, generated_at) for country, year in periods]
    files = [("00_overview.pdf", _overview_pdf(packages, today, generated_at))]
    for package in packages:
        files.extend((f"{period_folder(package)}/{name}", content) for name, content in package.files)
    return ClaimPackage(filename=f"SIGINT-VAT-refund-all-{today.isoformat()}.zip", content=_zip(files))
