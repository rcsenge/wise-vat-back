"""Generate the typed invoice PDF corpus for the extraction measurement.

The OLLAMA-LATENCY.md recommendation measures the rules path and the AI path on a
corpus of invoices. This script turns every golden invoice JSON in seed/invoices/ and
seed/sample_invoices/ into a typed PDF and an *.expected.json sidecar.

A typed PDF has a text layer. The rules path and the AI path both read the text layer.
The sidecar is the ground-truth ExtractedInvoice. The evaluator compares the extracted
invoice against the sidecar.

Run: uv run python -m seed.generate_documents
"""
import json
from pathlib import Path

from fpdf import FPDF

from app.schemas.invoice import ExtractedInvoice

BACKEND = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = BACKEND / "seed" / "documents"
INVOICES_DIR = BACKEND / "seed" / "invoices"
SAMPLE_INVOICES_DIR = BACKEND / "seed" / "sample_invoices"

PAGE_WIDTH = 210.0  # A4, in millimetres
MARGIN = 20.0
RIGHT = PAGE_WIDTH - MARGIN

FONT_REGULAR = "Roboto"
FONT_BOLD = "Roboto-Bold"


def _roboto_font_variants() -> dict[str, str]:
    """Return the Roboto regular and bold font file paths."""
    import font_roboto

    files = Path(font_roboto.__file__).parent / "files"
    return {
        FONT_REGULAR: str(files / "Roboto-Regular.ttf"),
        FONT_BOLD: str(files / "Roboto-Bold.ttf"),
    }


class InvoicePdf(FPDF):
    """A small A4 PDF helper that writes one invoice page."""

    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        variants = _roboto_font_variants()
        self.add_font(FONT_REGULAR, "", variants[FONT_REGULAR])
        self.add_font(FONT_BOLD, "", variants[FONT_BOLD])
        self.set_auto_page_break(auto=False)
        self.add_page()
        self.set_left_margin(MARGIN)
        self.set_right_margin(MARGIN)

    def _right_text(self, y: float, text: str, bold: bool = False, size: float = 10.0) -> None:
        self.set_font(FONT_BOLD if bold else FONT_REGULAR, size=size)
        self.set_xy(self.l_margin, y)
        self.cell(RIGHT - self.l_margin, 5.0, text, align="R")

    def _left_text(self, y: float, text: str, bold: bool = False, size: float = 10.0) -> None:
        self.set_font(FONT_BOLD if bold else FONT_REGULAR, size=size)
        self.set_xy(self.l_margin, y)
        self.cell(RIGHT - self.l_margin, 5.0, text, align="L")


def _text_currency_line(invoice: dict) -> str:
    """Return the paid-by-card footer line, or an empty string."""
    last4 = invoice.get("cardLast4")
    gross = invoice.get("totals", {}).get("grossAmount")
    currency = invoice.get("currency")
    if not last4 or gross is None or not currency:
        return ""
    return f"Paid by card **** {last4}: {gross} {currency}."


def _render_invoice(invoice: dict, pdf: InvoicePdf) -> None:
    supplier = invoice["supplier"]
    address = supplier["address"]
    y = 30.0

    pdf._left_text(y, supplier["name"], bold=True, size=13.0)
    y += 6.0
    if address.get("street"):
        pdf._left_text(y, address["street"])
        y += 5.0
    city_line = " ".join(part for part in (address.get("postalCode"), address.get("city")) if part)
    if city_line:
        pdf._left_text(y, f"{city_line}, {address.get('countryCode', '')}")
        y += 5.0
    if supplier.get("vatNumber"):
        pdf._left_text(y, f"VAT: {supplier['vatNumber']}")
        y += 5.0

    pdf._right_text(30.0, "INVOICE", bold=True, size=18.0)
    detail_y = 36.0
    details = [
        f"Invoice number: {invoice.get('invoiceNumber')}" if invoice.get("invoiceNumber") else None,
        f"Issue date: {invoice.get('issueDate')}" if invoice.get("issueDate") else None,
        f"Currency: {invoice.get('currency')}" if invoice.get("currency") else None,
    ]
    for detail in details:
        if detail:
            pdf._right_text(detail_y, detail)
            detail_y += 5.0

    y = max(y, detail_y) + 8.0
    customer = invoice.get("customer") or {}
    if customer.get("name"):
        y += 2.0
        pdf._left_text(y, "Rechnungsempfänger:")
        y += 5.0
        pdf._left_text(y, customer["name"])
        y += 5.0
        if customer.get("vatNumber"):
            pdf._left_text(y, f"VAT: {customer['vatNumber']}")
            y += 5.0

    y += 8.0
    # Column header
    header = ["Description", "Net", "VAT rate", "VAT", "Gross"]
    pdf._left_text(y, header[0], bold=True)
    _right_columns(pdf, y, header[1:])
    y += 6.0

    for line in invoice.get("lines", []):
        pdf._left_text(y, line.get("description", ""), size=9.0)
        _right_columns(pdf, y, [
            line.get("netAmount", ""),
            _rate_text(line.get("vatRate")),
            line.get("vatAmount", ""),
            line.get("grossAmount", ""),
        ], size=9.0)
        y += 6.0

    y += 4.0
    totals = invoice.get("totals", {})
    for label, key in (("Total net", "netAmount"), ("Total VAT", "vatAmount"), ("Total gross", "grossAmount")):
        pdf._left_text(y, label, bold=True)
        pdf._right_text(y, str(totals.get(key, "")), bold=True)
        y += 6.0

    footer = _text_currency_line(invoice)
    if footer:
        y += 8.0
        pdf._left_text(y, footer)


def _right_columns(pdf: InvoicePdf, y: float, values: list[str], size: float = 9.0) -> None:
    """Write the right-aligned numeric columns at the same row y."""
    pdf.set_font(FONT_REGULAR, size=size)
    # The columns sit at fixed x positions measured from the right edge.
    positions = [55.0, 35.0, 24.0, 0.0]
    for value, offset in zip(values, positions):
        pdf.set_xy(RIGHT - offset, y)
        pdf.cell(offset, 5.0, value, align="R")


def _rate_text(rate: object) -> str:
    """Return the VAT rate as a percent string, for example 10 or 7."""
    if rate is None:
        return ""
    return f"{rate} %"


def _invoice_files() -> list[Path]:
    """Return every golden invoice JSON, newest category first."""
    files = sorted(INVOICES_DIR.glob("*.json")) + sorted(SAMPLE_INVOICES_DIR.glob("*.json"))
    return files


def _write_sidecar(path: Path, invoice: dict) -> None:
    """Write the canonical ExtractedInvoice sidecar for the invoice."""
    parsed = ExtractedInvoice.model_validate(invoice)
    path.write_text(parsed.model_dump_json(by_alias=True, indent=2) + "\n", encoding="utf-8")


def generate(documents_dir: Path = DOCUMENTS_DIR) -> list[Path]:
    """Generate a PDF and a sidecar for every golden invoice. Return the written PDFs."""
    documents_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for invoice_file in _invoice_files():
        invoice = json.loads(invoice_file.read_text(encoding="utf-8"))
        stem = invoice_file.stem
        pdf_path = documents_dir / f"{stem}.pdf"
        sidecar_path = documents_dir / f"{stem}.expected.json"
        _write_sidecar(sidecar_path, invoice)

        # One PDF per page. Reuse the base font registry, then start a fresh page.
        renderer = InvoicePdf()
        _render_invoice(invoice, renderer)
        renderer.output(str(pdf_path))
        written.append(pdf_path)
    return written


def main() -> None:
    written = generate()
    print(f"Wrote {len(written)} corpus PDFs to {DOCUMENTS_DIR}")


if __name__ == "__main__":
    main()
