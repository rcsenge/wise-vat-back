"""Upload entry point tests. The upload takes only a PDF or a photo. A fake AI reads it."""
import io
import json
from decimal import Decimal

import pytest
from PIL import Image

from app.integrations.ollama_reader import get_invoice_reader
from app.main import app
from app.schemas.invoice import ExtractedInvoice
from tests.helpers import load_invoice

IMAGE_DATA_URL = "data:image/jpeg;base64,AAAA"
PDF_BYTES = b"%PDF-1.4 sample invoice"


def photo_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def ai_reads_vienna_hotel(client):
    """The fake AI returns the Vienna hotel invoice for every document."""
    invoice = ExtractedInvoice.model_validate(load_invoice("at_hotel_vienna.json"))
    app.dependency_overrides[get_invoice_reader] = lambda: lambda content, media_type: invoice


def upload(client, content: bytes, filename: str, content_type: str, **form):
    return client.post("/invoices/upload", files={"document": (filename, content, content_type)}, data=form)


def test_photo_upload_is_approved(client, ai_reads_vienna_hotel):
    response = upload(client, photo_bytes(), "receipt.jpg", "image/jpeg")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "approved"
    assert Decimal(body["country_totals"][0]["refundable_vat_total"]) == Decimal("26.00")


def test_pdf_upload_is_approved(client, ai_reads_vienna_hotel):
    response = upload(client, PDF_BYTES, "invoice.pdf", "application/pdf")
    assert response.json()["status"] == "approved"


def test_upload_stores_the_receipt_with_image(client, ai_reads_vienna_hotel):
    upload(client, photo_bytes(), "receipt.jpg", "image/jpeg", image_data_url=IMAGE_DATA_URL)
    receipts = client.get("/receipts").json()
    assert len(receipts) == 1
    assert receipts[0]["merchant"] == "Hotel Ringstrasse GmbH"
    assert receipts[0]["imageDataUrl"] == IMAGE_DATA_URL


def test_second_upload_of_same_invoice_is_rejected(client, ai_reads_vienna_hotel):
    upload(client, PDF_BYTES, "invoice.pdf", "application/pdf")
    body = upload(client, PDF_BYTES, "invoice.pdf", "application/pdf").json()
    assert body["status"] == "rejected"
    assert any("No matching" in reason for reason in body["reasons"])


def test_json_upload_is_rejected(client, ai_reads_vienna_hotel):
    content = json.dumps(load_invoice("at_hotel_vienna.json")).encode()
    response = upload(client, content, "invoice.json", "application/json")
    assert response.status_code == 415
    assert response.json()["detail"]["reasons"] == ["Upload a PDF or a photo of the invoice (JPEG, PNG, GIF or WebP)."]


def test_json_with_a_pdf_name_is_rejected(client, ai_reads_vienna_hotel):
    content = json.dumps(load_invoice("at_hotel_vienna.json")).encode()
    response = upload(client, content, "invoice.pdf", "application/pdf")
    assert response.status_code == 415


def test_unknown_document_type_is_rejected(client, ai_reads_vienna_hotel):
    response = upload(client, b"plain text", "notes.txt", "text/plain")
    assert response.status_code == 415


def test_upload_stores_the_original_document(client, engine, ai_reads_vienna_hotel):
    from sqlmodel import Session, select

    from app.models.invoice_document import InvoiceDocument
    from app.models.invoice_record import InvoiceRecord

    upload(client, PDF_BYTES, "hotel.pdf", "application/pdf")
    with Session(engine) as session:
        record = session.exec(select(InvoiceRecord)).one()
        stored = session.exec(select(InvoiceDocument)).one()
    assert stored.record_id == record.id
    assert stored.filename == "hotel.pdf"
    assert stored.media_type == "application/pdf"
    assert stored.content == PDF_BYTES
    assert '"vatNumber":"ATU12345678"' in record.invoice_json
