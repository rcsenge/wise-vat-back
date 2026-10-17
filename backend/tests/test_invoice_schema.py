"""The ExtractedInvoice contract: examples parse, and Pydantic and the JSON Schema file agree."""
import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.invoice import (
    Address,
    Customer,
    DocumentType,
    ExpenseCategory,
    ExtractedInvoice,
    InvoiceLine,
    Supplier,
    Totals,
)

BACKEND = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((BACKEND / "schemas" / "extracted_invoice.schema.json").read_text(encoding="utf-8"))
EXAMPLES = sorted((BACKEND / "seed" / "invoices").glob("*.json"))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_examples_parse(path: Path):
    invoice = ExtractedInvoice.model_validate(load(path))
    assert isinstance(invoice.totals.gross_amount, Decimal)


def test_examples_exist():
    assert len(EXAMPLES) >= 3


def test_amount_must_be_string_not_float():
    data = load(EXAMPLES[0])
    data["totals"]["grossAmount"] = 261.0
    with pytest.raises(ValidationError):
        ExtractedInvoice.model_validate(data)


def test_nullable_fields_must_still_be_present():
    data = load(EXAMPLES[0])
    del data["supplier"]["vatNumber"]
    with pytest.raises(ValidationError):
        ExtractedInvoice.model_validate(data)


def test_unknown_fields_are_rejected():
    data = load(EXAMPLES[0])
    data["confidence"] = 0.9
    with pytest.raises(ValidationError):
        ExtractedInvoice.model_validate(data)


def test_round_trip_uses_camel_case():
    invoice = ExtractedInvoice.model_validate(load(EXAMPLES[0]))
    dumped = invoice.model_dump(mode="json", by_alias=True)
    assert "issueDate" in dumped and "cardLast4" in dumped


MODEL_TO_SCHEMA_NODE = [
    (ExtractedInvoice, SCHEMA),
    (Supplier, SCHEMA["properties"]["supplier"]),
    (Address, SCHEMA["properties"]["supplier"]["properties"]["address"]),
    (Customer, SCHEMA["properties"]["customer"]),
    (InvoiceLine, SCHEMA["properties"]["lines"]["items"]),
    (Totals, SCHEMA["properties"]["totals"]),
]


@pytest.mark.parametrize("model,node", MODEL_TO_SCHEMA_NODE, ids=lambda x: getattr(x, "__name__", ""))
def test_json_schema_file_matches_pydantic(model: type[BaseModel], node: dict):
    aliases = {f.alias for f in model.model_fields.values()}
    required = {f.alias for f in model.model_fields.values() if f.is_required()}
    assert set(node["properties"]) == aliases
    assert set(node["required"]) == required
    assert node["additionalProperties"] is False


def test_enums_match():
    assert SCHEMA["properties"]["documentType"]["enum"] == [e.value for e in DocumentType]
    # Order matters: index + 1 is the Directive 2008/9/EC refund code.
    assert SCHEMA["properties"]["lines"]["items"]["properties"]["category"]["enum"] == [e.value for e in ExpenseCategory]
