"""Generate the sample invoice PDFs in seed/documents/.

The passing invoice matches a seeded German card transaction. The failing invoice
has no supplier VAT number, so the backend rejects it.

Run: uv run --with reportlab python -m seed.make_documents
"""
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

DOCUMENTS_DIR = Path(__file__).resolve().parent / "documents"


@dataclass(frozen=True)
class Line:
    description: str
    quantity: str
    net: str
    rate: str
    vat: str
    gross: str


@dataclass(frozen=True)
class Invoice:
    file_name: str
    title: str
    supplier: list[str]
    customer: list[str]
    details: list[tuple[str, str]]
    lines: list[Line]
    totals: list[tuple[str, str]]
    footer: list[str]


PASSING = Invoice(
    file_name="pass_de_hotel_berlin.pdf",
    title="RECHNUNG",
    supplier=[
        "Hotel Spreeufer Berlin GmbH",
        "Friedrichstraße 112",
        "10117 Berlin, Deutschland",
        "USt-IdNr.: DE298765432",
    ],
    customer=["Rechnungsempfänger:", "Példa Tech Kft.", "Váci út 45, 1134 Budapest, Ungarn", "USt-IdNr.: HU12345678"],
    details=[("Rechnungsnummer", "2026-10-0441"), ("Rechnungsdatum", "14.10.2026"), ("Aufenthalt", "12.10.2026 - 14.10.2026")],
    lines=[
        Line("Übernachtung Einzelzimmer (2 Nächte à 120,00)", "2", "240,00", "7 %", "16,80", "256,80"),
        Line("Frühstück (2 × 15,00)", "2", "30,00", "19 %", "5,70", "35,70"),
    ],
    totals=[("Summe netto", "270,00 EUR"), ("USt. 7 %", "16,80 EUR"), ("USt. 19 %", "5,70 EUR"), ("Gesamtbetrag", "292,50 EUR")],
    footer=["Bezahlt mit Visa **** 4821 am 14.10.2026: 292,50 EUR.", "Vielen Dank für Ihren Aufenthalt."],
)

FAILING = Invoice(
    file_name="fail_at_restaurant_no_vat_number.pdf",
    title="RECHNUNG / KASSENBON",
    supplier=["Gasthaus Zum Goldenen Hirschen", "Getreidegasse 9", "5020 Salzburg, Österreich", "Tel. +43 662 000 000"],
    customer=[],
    details=[("Bon-Nr.", "4711"), ("Datum", "11.10.2026 19:42"), ("Tisch", "7")],
    lines=[
        Line("Wiener Schnitzel mit Erdäpfelsalat", "2", "35,45", "10 %", "3,55", "39,00"),
        Line("Almdudler 0,5 l", "2", "7,00", "20 %", "1,40", "8,40"),
    ],
    totals=[("Summe netto", "42,45 EUR"), ("MwSt. 10 %", "3,55 EUR"), ("MwSt. 20 %", "1,40 EUR"), ("Gesamt", "47,40 EUR")],
    footer=["Bezahlt mit Mastercard **** 4821: 47,40 EUR.", "Danke für Ihren Besuch!"],
)


def draw(invoice: Invoice) -> Path:
    path = DOCUMENTS_DIR / invoice.file_name
    canvas = Canvas(str(path), pagesize=A4)
    width, height = A4
    left, right = 20 * mm, width - 20 * mm

    y = height - 25 * mm
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(left, y, invoice.supplier[0])
    canvas.setFont("Helvetica", 9)
    for text in invoice.supplier[1:]:
        y -= 5 * mm
        canvas.drawString(left, y, text)

    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawRightString(right, height - 25 * mm, invoice.title)
    detail_y = height - 33 * mm
    canvas.setFont("Helvetica", 9)
    for label, value in invoice.details:
        canvas.drawRightString(right - 42 * mm, detail_y, f"{label}:")
        canvas.drawRightString(right, detail_y, value)
        detail_y -= 5 * mm

    y = min(y, detail_y) - 12 * mm
    for index, text in enumerate(invoice.customer):
        canvas.setFont("Helvetica-Bold" if index == 1 else "Helvetica", 9)
        canvas.drawString(left, y, text)
        y -= 5 * mm

    y -= 8 * mm
    columns = [(left, "Bezeichnung"), (right - 78 * mm, "Menge"), (right - 60 * mm, "Netto"), (right - 42 * mm, "USt."), (right - 24 * mm, "Steuer"), (right, "Brutto")]
    canvas.setFillColor(colors.HexColor("#163300"))
    canvas.rect(left - 2 * mm, y - 2.5 * mm, right - left + 4 * mm, 8 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    for index, (x, label) in enumerate(columns):
        (canvas.drawString if index == 0 else canvas.drawRightString)(x, y, label)
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica", 9)
    for line in invoice.lines:
        y -= 8 * mm
        values = [line.description, line.quantity, line.net, line.rate, line.vat, line.gross]
        for index, ((x, _), value) in enumerate(zip(columns, values)):
            (canvas.drawString if index == 0 else canvas.drawRightString)(x, y, value)

    y -= 6 * mm
    canvas.line(left, y, right, y)
    for index, (label, value) in enumerate(invoice.totals):
        y -= 6 * mm
        is_total = index == len(invoice.totals) - 1
        canvas.setFont("Helvetica-Bold" if is_total else "Helvetica", 10 if is_total else 9)
        canvas.drawRightString(right - 30 * mm, y, label)
        canvas.drawRightString(right, y, value)

    y -= 16 * mm
    canvas.setFont("Helvetica", 9)
    for text in invoice.footer:
        canvas.drawString(left, y, text)
        y -= 5 * mm

    canvas.showPage()
    canvas.save()
    return path


def run() -> None:
    DOCUMENTS_DIR.mkdir(exist_ok=True)
    for invoice in (PASSING, FAILING):
        print(f"Wrote {draw(invoice)}")


if __name__ == "__main__":
    run()
