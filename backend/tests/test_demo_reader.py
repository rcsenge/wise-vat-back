"""The demo invoice reader: every upload becomes the Berlin hotel invoice and passes."""
import time
from pathlib import Path

from app.config import settings
from app.integrations.demo_reader import DemoInvoiceReader
from app.integrations.ollama_reader import get_invoice_reader
from app.main import app

DOCUMENTS_DIR = Path(__file__).resolve().parents[1] / "seed" / "documents"
JPEG_PHOTO = b"\xff\xd8\xff\xe0" + b"photo" * 10


def use_demo_reader(delay_seconds: float = 0.0) -> None:
    app.dependency_overrides[get_invoice_reader] = lambda: DemoInvoiceReader(delay_seconds)


def upload_photo(client) -> dict:
    return client.post("/invoices/upload", files={"document": ("photo.jpg", JPEG_PHOTO, "image/jpeg")}).json()


def test_demo_reader_waits_and_returns_the_berlin_invoice():
    started = time.monotonic()
    invoice = DemoInvoiceReader(0.2)(JPEG_PHOTO, "image/jpeg")
    assert time.monotonic() - started >= 0.2
    assert invoice.invoice_number == "2026-10-0441"
    assert invoice.supplier.name == "Hotel Spreeufer Berlin GmbH"
    assert str(invoice.totals.gross_amount) == "292.50"


def test_any_photo_passes_with_the_demo_reader(client):
    use_demo_reader()
    body = upload_photo(client)
    assert body["status"] == "approved"
    assert body["invoice_number"] == "2026-10-0441"


def test_the_demo_upload_passes_again_and_again(client):
    use_demo_reader()
    for _ in range(3):
        assert upload_photo(client)["status"] == "approved"
    receipts = client.get("/receipts").json()
    assert sum(1 for receipt in receipts if receipt["merchant"] == "Hotel Spreeufer Berlin GmbH") == 1


def test_the_demo_reader_still_rejects_a_json_file(client):
    use_demo_reader()
    response = client.post("/invoices/upload", files={"document": ("invoice.json", b'{"a": 1}', "application/json")})
    assert response.status_code == 415


def test_settings_select_the_demo_reader_by_default(monkeypatch):
    get_invoice_reader.cache_clear()
    monkeypatch.setattr(settings, "invoice_reader", "demo")
    try:
        assert isinstance(get_invoice_reader(), DemoInvoiceReader)
    finally:
        get_invoice_reader.cache_clear()
