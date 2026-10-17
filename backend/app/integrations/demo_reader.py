"""The demo invoice reader. It replaces the AI for the live demo.

Every PDF or photo becomes the Berlin hotel invoice of the printed demo copy.
The reader waits a short time. The upload then looks like a real reading.
"""
import time
from pathlib import Path

from app.schemas.invoice import ExtractedInvoice

DEMO_INVOICE_PATH = Path(__file__).resolve().parents[2] / "seed" / "documents" / "pass_de_hotel_berlin.expected.json"


def load_demo_invoice() -> ExtractedInvoice:
    return ExtractedInvoice.model_validate_json(DEMO_INVOICE_PATH.read_text(encoding="utf-8"))


class DemoInvoiceReader:
    def __init__(self, delay_seconds: float) -> None:
        self._delay_seconds = delay_seconds

    def __call__(self, content: bytes, media_type: str) -> ExtractedInvoice:
        time.sleep(self._delay_seconds)
        return load_demo_invoice()
