"""Turn an uploaded document into an ExtractedInvoice.

The upload accepts only a PDF or a photo. The local AI reader turns it into the invoice
contract. A JSON invoice goes only to POST /invoices, never to the upload.
"""
from app.integrations.ollama_reader import InvoiceReader, ReaderError
from app.schemas.invoice import ExtractedInvoice

MAX_DOCUMENT_BYTES = 20_000_000

# The file signature decides the type. The browser content type can be empty or wrong.
SIGNATURES = (
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)
UNSUPPORTED_DOCUMENT_REASON = "Upload a PDF or a photo of the invoice (JPEG, PNG, GIF or WebP)."


class DocumentError(ValueError):
    """The uploaded document cannot become an ExtractedInvoice."""

    def __init__(self, status_code: int, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.status_code = status_code
        self.reasons = reasons


def detect_media_type(content: bytes) -> str | None:
    """Return the media type of a PDF or an image, or None for any other document."""
    for signature, media_type in SIGNATURES:
        if content.startswith(signature):
            return media_type
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def extract_invoice(content: bytes, read_with_ai: InvoiceReader) -> ExtractedInvoice:
    """Return the invoice in the PDF or photo. Raise DocumentError with readable reasons."""
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentError(413, [f"The document is larger than {MAX_DOCUMENT_BYTES // 1_000_000} MB."])
    media_type = detect_media_type(content)
    if media_type is None:
        raise DocumentError(415, [UNSUPPORTED_DOCUMENT_REASON])
    try:
        return read_with_ai(content, media_type)
    except ReaderError as error:
        raise DocumentError(error.status_code, error.reasons) from error
