"""Turn an uploaded document into an ExtractedInvoice.

The demo accepts only a JSON file in the ExtractedInvoice shape. The AI step replaces
this module later: it reads a receipt image and returns the same contract. The upload
endpoint and the frontend stay the same.
"""
from pydantic import ValidationError

from app.schemas.invoice import ExtractedInvoice

MAX_DOCUMENT_BYTES = 1_000_000
JSON_CONTENT_TYPES = {"application/json", "text/json"}


class DocumentError(ValueError):
    """The uploaded document cannot become an ExtractedInvoice."""

    def __init__(self, status_code: int, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.status_code = status_code
        self.reasons = reasons


def is_json_document(content_type: str | None, filename: str | None) -> bool:
    if content_type and content_type.split(";")[0].strip() in JSON_CONTENT_TYPES:
        return True
    return bool(filename) and filename.lower().endswith(".json")


def extract_invoice(content: bytes, content_type: str | None, filename: str | None) -> ExtractedInvoice:
    """Return the invoice in the document. Raise DocumentError with readable reasons."""
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentError(413, [f"The document is larger than {MAX_DOCUMENT_BYTES} bytes."])
    if not is_json_document(content_type, filename):
        raise DocumentError(415, ["Upload an invoice JSON file. Image extraction is not available yet."])
    try:
        return ExtractedInvoice.model_validate_json(content)
    except ValidationError as error:
        raise DocumentError(422, [_reason(item) for item in error.errors()]) from error


def _reason(item: dict) -> str:
    location = ".".join(str(part) for part in item["loc"])
    return f"{location}: {item['msg']}" if location else item["msg"]
