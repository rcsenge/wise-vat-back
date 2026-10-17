"""Test helpers. Load the hardcoded seed invoices as dictionaries."""
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
INVOICES_DIR = BACKEND / "seed" / "invoices"


def load_invoice(name: str) -> dict:
    return json.loads((INVOICES_DIR / name).read_text(encoding="utf-8"))
