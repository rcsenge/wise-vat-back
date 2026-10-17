"""Turn an uploaded document into an ExtractedInvoice.

A JSON file in the ExtractedInvoice shape is read directly. A PDF or a photo goes
to the local AI reader. Both paths return the same contract.
"""
from pydantic import ValidationError

from app.integrations.ollama_reader import InvoiceReader, ReaderError
from app.schemas.invoice import ExtractedInvoice

MAX_DOCUMENT_BYTES = 20_000_000
JSON_CONTENT_TYPES = {"application/json", "text/json"}

# The file signature decides the type. The browser content type can be empty or wrong.
SIGNATURES = (
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)


class DocumentError(ValueError):
    """The uploaded document cannot become an ExtractedInvoice."""

    def __init__(self, status_code: int, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.status_code = status_code
        self.reasons = reasons


def detect_media_type(content: bytes, content_type: str | None, filename: str | None) -> str | None:
    """Return the media type of the document, or None for an unsupported document."""
    for signature, media_type in SIGNATURES:
        if content.startswith(signature):
            return media_type
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    if content_type and content_type.split(";")[0].strip() in JSON_CONTENT_TYPES:
        return "application/json"
    if filename and filename.lower().endswith(".json"):
        return "application/json"
    return None


def extract_invoice(
    content: bytes, content_type: str | None, filename: str | None, read_with_ai: InvoiceReader
) -> ExtractedInvoice:
    """Return the invoice in the document. Raise DocumentError with readable reasons."""
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentError(413, [f"The document is larger than {MAX_DOCUMENT_BYTES // 1_000_000} MB."])
    media_type = detect_media_type(content, content_type, filename)
    if media_type is None:
        raise DocumentError(415, ["Upload a PDF, a photo (JPEG, PNG, GIF, WebP) or an invoice JSON file."])
    if media_type == "application/json":
        return _read_json(content)
    try:
        return read_with_ai(content, media_type)
    except ReaderError as error:
        raise DocumentError(error.status_code, error.reasons) from error


def _read_json(content: bytes) -> ExtractedInvoice:
    try:
        return ExtractedInvoice.model_validate_json(content)
    except ValidationError as error:
        raise DocumentError(422, [_reason(item) for item in error.errors()]) from error


def _reason(item: dict) -> str:
    location = ".".join(str(part) for part in item["loc"])
    return f"{location}: {item['msg']}" if location else item["msg"]
