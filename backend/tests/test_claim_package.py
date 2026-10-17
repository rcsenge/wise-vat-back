"""The claim package: one ZIP per refund country and year, ready for the accountant."""
import csv
import io
import json
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pypdfium2

from app.config import settings
from app.integrations.ollama_reader import get_invoice_reader
from app.main import app
from app.schemas.invoice import ExtractedInvoice
from tests.helpers import load_invoice

DOCUMENTS_DIR = Path(__file__).resolve().parents[1] / "seed" / "documents"
BERLIN_PDF = DOCUMENTS_DIR / "pass_de_hotel_berlin.pdf"


def upload_berlin_pdf(client) -> None:
    expected = BERLIN_PDF.with_suffix(".expected.json").read_text(encoding="utf-8")
    app.dependency_overrides[get_invoice_reader] = lambda: lambda content, media_type: (
        ExtractedInvoice.model_validate_json(expected)
    )
    response = client.post("/invoices/upload", files={"document": (BERLIN_PDF.name, BERLIN_PDF.read_bytes(), "application/pdf")})
    assert response.json()["status"] == "approved"


def download(client, country: str, year: int) -> zipfile.ZipFile:
    response = client.get("/claims/package", params={"country": country, "year": year})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert f'filename="SIGINT-VAT-refund-{country}-{year}.zip"' in response.headers["content-disposition"]
    return zipfile.ZipFile(io.BytesIO(response.content))


def read_csv(archive: zipfile.ZipFile, name: str) -> list[dict]:
    text = archive.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


def pdf_text(content: bytes) -> str:
    document = pypdfium2.PdfDocument(content)
    return "\n".join(document[index].get_textpage().get_text_bounded() for index in range(len(document)))


def test_package_holds_every_file(client):
    upload_berlin_pdf(client)
    archive = download(client, "DE", 2026)
    assert set(archive.namelist()) == {
        "00_summary.pdf",
        "01_refund_application_lines.csv",
        "02_invoice_copies/001_2026-10-0441.pdf",
        "03_card_transactions.csv",
        "04_decision_log.csv",
        "05_application_data.json",
    }
    assert archive.read("02_invoice_copies/001_2026-10-0441.pdf") == BERLIN_PDF.read_bytes()


def test_lines_file_has_the_form_fields_and_codes(client):
    upload_berlin_pdf(client)
    rows = read_csv(download(client, "DE", 2026), "01_refund_application_lines.csv")
    assert [(row["goods_services_code"], row["deductible_vat"]) for row in rows] == [("6", "16.80"), ("7", "5.70")]
    first = rows[0]
    assert first["supplier_name"] == "Hotel Spreeufer Berlin GmbH"
    assert first["supplier_vat_number"] == "DE298765432"
    assert first["invoice_number"] == "2026-10-0441"
    assert first["issue_date"] == "2026-10-14"
    assert first["currency"] == "EUR"
    assert first["deductible_share_percent"] == "100"


def test_summary_pdf_shows_the_total_and_the_deadline(client):
    upload_berlin_pdf(client)
    text = pdf_text(download(client, "DE", 2026).read("00_summary.pdf"))
    assert "VAT refund application package" in text
    assert "22.50 EUR" in text
    assert "30 September 2027" in text
    assert settings.applicant_name in text
    assert "Hotel Spreeufer Berlin GmbH" in text


def test_json_and_logs_match_the_invoice(client):
    upload_berlin_pdf(client)
    archive = download(client, "DE", 2026)
    data = json.loads(archive.read("05_application_data.json"))
    assert data["member_state_of_refund"] == "DE"
    assert data["refund_period"] == {"start": "2026-01-01", "end": "2026-12-31"}
    assert Decimal(data["deductible_vat_total"]) == Decimal("22.50")
    assert data["applicant"]["vat_number"] == settings.applicant_vat_number
    payments = read_csv(archive, "03_card_transactions.csv")
    assert payments[0]["amount"] == "292.50"
    decisions = {row["check"]: row["result"] for row in read_csv(archive, "04_decision_log.csv")}
    assert decisions["VIES"] == "passed"
    assert decisions["card payment"] == "matched"
    assert decisions["decision"] == "approved"


def test_invoice_without_upload_gets_a_copy_warning(client):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    archive = download(client, "AT", 2026)
    assert not [name for name in archive.namelist() if name.startswith("02_invoice_copies/")]
    text = pdf_text(archive.read("00_summary.pdf"))
    assert "Rows 1 have no original copy in the package." in text


def test_expired_period_package_warns_about_the_deadline(client, monkeypatch):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    monkeypatch.setattr(settings, "claim_reference_date", date(2027, 10, 1))
    text = pdf_text(download(client, "AT", 2026).read("00_summary.pdf"))
    assert "The deadline passed on 30 September 2027." in text


def test_no_invoices_gives_404(client):
    response = client.get("/claims/package", params={"country": "FR", "year": 2026})
    assert response.status_code == 404
    assert response.json()["detail"]["reasons"] == ["There are no approved invoices for France in 2026."]


def test_bad_country_code_is_rejected(client):
    assert client.get("/claims/package", params={"country": "france", "year": 2026}).status_code == 422
