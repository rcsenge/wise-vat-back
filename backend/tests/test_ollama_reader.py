"""Local AI reader tests. A fake Ollama server stands in for the network."""
import base64
import io
import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app.integrations.ollama_reader import (
    SCHEMA_KEYS_TO_DROP,
    OllamaInvoiceReader,
    ReaderError,
    build_output_schema,
    get_invoice_reader,
)
from app.main import app
from app.schemas.invoice import ExtractedInvoice
from tests.helpers import load_invoice

DOCUMENTS_DIR = Path(__file__).resolve().parents[1] / "seed" / "documents"
PASSING_PDF = DOCUMENTS_DIR / "pass_de_hotel_berlin.pdf"
FAILING_PDF = DOCUMENTS_DIR / "fail_at_restaurant_no_vat_number.pdf"
OLLAMA_URL = "http://ollama.test"


def photo_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (3000, 2000), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def expected_json(pdf: Path) -> str:
    return pdf.with_suffix(".expected.json").read_text(encoding="utf-8")


def fake_reader(handler) -> tuple[OllamaInvoiceReader, list[dict]]:
    """Return a reader that talks to a fake Ollama. The list collects the request bodies."""
    requests: list[dict] = []

    def record(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record))
    return OllamaInvoiceReader(client, OLLAMA_URL, "qwen2.5vl:7b"), requests


def answer(content: str) -> httpx.Response:
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}, "done": True})


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def test_output_schema_keeps_structure_and_drops_patterns():
    schema = build_output_schema()
    assert "totals" in schema["required"]
    for node in walk(schema):
        assert not SCHEMA_KEYS_TO_DROP & node.keys()


def test_pdf_request_sends_page_images_text_and_schema():
    reader, requests = fake_reader(lambda request: answer(expected_json(PASSING_PDF)))
    invoice = reader(PASSING_PDF.read_bytes(), "application/pdf")
    assert invoice.supplier.name == "Hotel Spreeufer Berlin GmbH"
    body = requests[0]
    assert body["model"] == "qwen2.5vl:7b"
    assert body["stream"] is False
    assert body["format"]["type"] == "object"
    user_message = body["messages"][1]
    assert len(user_message["images"]) == 1
    assert "DE298765432" in user_message["content"]


def test_photo_is_shrunk_before_sending():
    reader, requests = fake_reader(lambda request: answer(json.dumps(load_invoice("at_hotel_vienna.json"))))
    reader(photo_bytes(), "image/png")
    image_bytes = base64.b64decode(requests[0]["messages"][1]["images"][0])
    with Image.open(io.BytesIO(image_bytes)) as image:
        assert max(image.size) == 2000
        assert image.format == "JPEG"


def test_ollama_not_running_gives_a_clear_reason():
    def refuse(request):
        raise httpx.ConnectError("connection refused", request=request)

    reader, _ = fake_reader(refuse)
    with pytest.raises(ReaderError) as caught:
        reader(photo_bytes(), "image/png")
    assert caught.value.status_code == 503
    assert "Start Ollama" in caught.value.reasons[0]


def test_missing_model_tells_how_to_pull_it():
    reader, _ = fake_reader(lambda request: httpx.Response(404, json={"error": "model not found"}))
    with pytest.raises(ReaderError) as caught:
        reader(photo_bytes(), "image/png")
    assert caught.value.reasons == ["The model qwen2.5vl:7b is missing. Run: ollama pull qwen2.5vl:7b"]


def test_text_that_is_not_json_is_rejected():
    reader, _ = fake_reader(lambda request: answer("I cannot read this."))
    with pytest.raises(ReaderError) as caught:
        reader(photo_bytes(), "image/png")
    assert caught.value.status_code == 422


def test_invalid_ai_output_is_reported():
    data = load_invoice("at_hotel_vienna.json")
    data["totals"]["grossAmount"] = "261,00"
    reader, _ = fake_reader(lambda request: answer(json.dumps(data)))
    with pytest.raises(ReaderError) as caught:
        reader(photo_bytes(), "image/png")
    assert any("grossAmount" in reason for reason in caught.value.reasons)


def test_broken_pdf_is_rejected():
    reader, _ = fake_reader(lambda request: answer("{}"))
    with pytest.raises(ReaderError) as caught:
        reader(b"%PDF-1.4 broken", "application/pdf")
    assert caught.value.reasons == ["The PDF cannot be opened."]


def upload_pdf(client, pdf: Path) -> dict:
    """Upload a sample PDF. The fake AI returns the expected extraction for it."""
    expected = expected_json(pdf)
    app.dependency_overrides[get_invoice_reader] = lambda: lambda content, media_type: (
        ExtractedInvoice.model_validate_json(expected)
    )
    return client.post("/invoices/upload", files={"document": (pdf.name, pdf.read_bytes(), "application/pdf")}).json()


def test_sample_pdf_passes(client):
    body = upload_pdf(client, PASSING_PDF)
    assert body["status"] == "approved"
    assert body["matched_transaction"]["merchant"] == "Hotel Spreeufer Berlin GmbH"
    assert Decimal(body["country_totals"][0]["refundable_vat_total"]) == Decimal("22.50")


def test_sample_pdf_fails_without_vat_number(client):
    body = upload_pdf(client, FAILING_PDF)
    assert body["status"] == "rejected"
    assert body["reasons"] == ["The invoice has no supplier VAT number."]


def test_reader_error_reaches_the_frontend(client):
    def unavailable(content, media_type):
        raise ReaderError(503, ["The local AI is not running at http://localhost:11434. Start Ollama on this machine."])

    app.dependency_overrides[get_invoice_reader] = lambda: unavailable
    response = client.post("/invoices/upload", files={"document": ("scan.pdf", PASSING_PDF.read_bytes(), "application/octet-stream")})
    assert response.status_code == 503
    assert "Start Ollama" in response.json()["detail"]["reasons"][0]
