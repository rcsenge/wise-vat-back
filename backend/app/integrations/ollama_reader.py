"""Read an invoice PDF or photo with a local Ollama vision model.

Ollama runs on the same machine as the backend. It needs no API key and has no usage limit.
The request sends the ExtractedInvoice JSON Schema in the "format" field. Ollama then
constrains the model output to that schema. Pydantic validates the result again.
"""
import base64
import io
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

import httpx
import pypdfium2
from PIL import Image
from pydantic import ValidationError

from app.config import settings
from app.schemas.invoice import ExtractedInvoice

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "extracted_invoice.schema.json"
MAX_PDF_PAGES = 3
PDF_RENDER_SCALE = 2  # 144 DPI. The model reads small print reliably at this scale.
MAX_IMAGE_DIMENSION = 2000
JPEG_QUALITY = 90
MAX_PDF_TEXT_CHARACTERS = 20_000
CONTEXT_TOKENS = 16384  # Room for three page images, the PDF text and the JSON answer
KEEP_ALIVE = "10m"  # Keep the model in memory between uploads

# Ollama does not need these keywords. Pydantic checks them after the call.
SCHEMA_KEYS_TO_DROP = {"$schema", "$id", "pattern"}

SYSTEM_PROMPT = """You read invoices and receipts for an EU VAT refund service.
Copy the facts printed on the document into the JSON schema. Never invent a value.
If a field is not on the document, return null for it. A missing supplier VAT number must stay null.

Field rules:
- schemaVersion is always "1.0".
- documentType is FULL_INVOICE when the document names the buyer. Otherwise SIMPLIFIED_INVOICE.
- issueDate uses the format YYYY-MM-DD.
- currency is the ISO 4217 code. countryCode is the ISO 3166-1 alpha-2 code of the supplier address.
- VAT numbers have the country prefix and no spaces, for example ATU12345678 or DE123456789.
- Amounts are decimal strings with a dot and two decimals, for example "188.80". vatRate is a percent number, for example 10.
- Give one line per invoice item. If the document shows only totals, give one line with the totals.
- category is the expense code: FUEL, VEHICLE_HIRE, VEHICLE_EXPENSES, ROAD_TOLL,
  TRAVEL (taxi, train, flight), ACCOMMODATION (hotel room), FOOD_AND_DRINK (meals, breakfast, drinks),
  FAIR_ADMISSION, ENTERTAINMENT (shows, clubs, leisure), or OTHER (for example parking or garage).
- cardLast4 holds the last four card digits when the document shows a card payment."""


class ReaderError(Exception):
    """The local AI could not turn the document into an invoice."""

    def __init__(self, status_code: int, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.status_code = status_code
        self.reasons = reasons


class InvoiceReader(Protocol):
    def __call__(self, content: bytes, media_type: str) -> ExtractedInvoice: ...


def _drop_keys(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: _drop_keys(value) for key, value in node.items() if key not in SCHEMA_KEYS_TO_DROP}
    if isinstance(node, list):
        return [_drop_keys(item) for item in node]
    return node


def build_output_schema() -> dict[str, Any]:
    return _drop_keys(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def _encode_image(image: Image.Image) -> str:
    image = image.convert("RGB")
    image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return base64.standard_b64encode(buffer.getvalue()).decode("ascii")


def prepare_pdf(content: bytes) -> tuple[list[str], str]:
    """Return the first pages as base64 JPEG images and the text layer of the PDF."""
    try:
        document = pypdfium2.PdfDocument(content)
    except pypdfium2.PdfiumError as error:
        raise ReaderError(422, ["The PDF cannot be opened."]) from error
    images: list[str] = []
    texts: list[str] = []
    try:
        for index in range(min(len(document), MAX_PDF_PAGES)):
            page = document[index]
            images.append(_encode_image(page.render(scale=PDF_RENDER_SCALE).to_pil()))
            texts.append(page.get_textpage().get_text_bounded())
    finally:
        document.close()
    return images, "\n".join(texts).strip()[:MAX_PDF_TEXT_CHARACTERS]


def prepare_photo(content: bytes) -> list[str]:
    try:
        with Image.open(io.BytesIO(content)) as image:
            return [_encode_image(image)]
    except OSError as error:
        raise ReaderError(422, ["The photo cannot be opened."]) from error


def _user_message(images: list[str], pdf_text: str) -> dict[str, Any]:
    text = "Extract this invoice."
    if pdf_text:
        text += f"\n\nThe text layer of the PDF follows. Prefer it for exact numbers.\n\n{pdf_text}"
    return {"role": "user", "content": text, "images": images}


class OllamaInvoiceReader:
    def __init__(self, client: httpx.Client, base_url: str, model: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._output_schema = build_output_schema()

    def __call__(self, content: bytes, media_type: str) -> ExtractedInvoice:
        if media_type == "application/pdf":
            images, pdf_text = prepare_pdf(content)
        else:
            images, pdf_text = prepare_photo(content), ""
        body = {
            "model": self._model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, _user_message(images, pdf_text)],
            "format": self._output_schema,
            "stream": False,
            "keep_alive": KEEP_ALIVE,
            "options": {"temperature": 0, "num_ctx": CONTEXT_TOKENS},
        }
        try:
            response = self._client.post(f"{self._base_url}/api/chat", json=body)
        except httpx.ConnectError as error:
            raise ReaderError(
                503, [f"The local AI is not running at {self._base_url}. Start Ollama on this machine."]
            ) from error
        except httpx.TimeoutException as error:
            raise ReaderError(504, ["The local AI did not answer in time. Try again."]) from error
        if response.status_code == 404:
            raise ReaderError(503, [f"The model {self._model} is missing. Run: ollama pull {self._model}"])
        if response.status_code != 200:
            raise ReaderError(502, [f"The local AI returned status {response.status_code}: {_error_text(response)}"])
        return _parse_answer(response.json())


def _error_text(response: httpx.Response) -> str:
    try:
        return str(response.json().get("error", ""))
    except ValueError:
        return response.text[:200]


def _parse_answer(answer: dict[str, Any]) -> ExtractedInvoice:
    content = answer.get("message", {}).get("content", "")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as error:
        raise ReaderError(422, ["The local AI returned text that is not JSON."]) from error
    try:
        return ExtractedInvoice.model_validate(data)
    except ValidationError as error:
        reasons = [f"AI output {'.'.join(str(part) for part in item['loc'])}: {item['msg']}" for item in error.errors()]
        raise ReaderError(422, reasons) from error


@lru_cache
def get_invoice_reader() -> InvoiceReader:
    client = httpx.Client(timeout=settings.ollama_timeout_seconds)
    return OllamaInvoiceReader(client, settings.ollama_url, settings.ollama_model)
