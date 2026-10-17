"""ExtractedInvoice: what the receipt/invoice image processing hands to the backend.

Source of truth for the contract. backend/schemas/extracted_invoice.schema.json is the
same contract as plain JSON Schema for the image-processing side; tests keep them in sync.

Nullable fields are still required: null means "not on the document" (e.g. a missing
supplier VAT number is what turns an item red). Arithmetic consistency is NOT checked
here; that is a domain rule, so a bad OCR result gets an explained decision, not a 422.
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pydantic.alias_generators import to_camel

SCHEMA_VERSION = "1.0"

AMOUNT_PATTERN = r"^-?\d+(\.\d{1,2})?$"
VAT_NUMBER_PATTERN = r"^[A-Z]{2}[0-9A-Z]{2,13}$"


def _amount_from_string(value: object) -> object:
    # Amounts travel as strings ("188.80") so they never pass through a float.
    if not isinstance(value, str):
        raise ValueError("amount must be a decimal string, e.g. \"188.80\"")
    return value


Amount = Annotated[Decimal, BeforeValidator(_amount_from_string), Field(json_schema_extra={"pattern": AMOUNT_PATTERN})]
VatNumber = Annotated[str, Field(pattern=VAT_NUMBER_PATTERN)]


class _Contract(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class DocumentType(str, Enum):
    FULL_INVOICE = "FULL_INVOICE"
    SIMPLIFIED_INVOICE = "SIMPLIFIED_INVOICE"


class ExpenseCategory(str, Enum):
    """One-to-one with the refund application codes of Directive 2008/9/EC, Art. 9."""

    FUEL = "FUEL"                          # 1
    VEHICLE_HIRE = "VEHICLE_HIRE"          # 2
    VEHICLE_EXPENSES = "VEHICLE_EXPENSES"  # 3
    ROAD_TOLL = "ROAD_TOLL"                # 4
    TRAVEL = "TRAVEL"                      # 5
    ACCOMMODATION = "ACCOMMODATION"        # 6
    FOOD_AND_DRINK = "FOOD_AND_DRINK"      # 7
    FAIR_ADMISSION = "FAIR_ADMISSION"      # 8
    ENTERTAINMENT = "ENTERTAINMENT"        # 9
    OTHER = "OTHER"                        # 10


class Address(_Contract):
    street: str | None
    postal_code: str | None
    city: str | None
    country_code: str = Field(pattern=r"^[A-Z]{2}$")


class Supplier(_Contract):
    name: str = Field(min_length=1)
    vat_number: VatNumber | None
    address: Address


class Customer(_Contract):
    name: str | None
    vat_number: VatNumber | None


class InvoiceLine(_Contract):
    description: str = Field(min_length=1)
    category: ExpenseCategory
    net_amount: Amount
    vat_rate: Decimal = Field(ge=0, le=100)
    vat_amount: Amount
    gross_amount: Amount


class Totals(_Contract):
    net_amount: Amount
    vat_amount: Amount
    gross_amount: Amount


class ExtractedInvoice(_Contract):
    schema_version: Literal["1.0"]
    document_type: DocumentType
    invoice_number: str | None
    issue_date: date
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    supplier: Supplier
    customer: Customer
    lines: list[InvoiceLine] = Field(min_length=1)
    totals: Totals
    card_last4: str | None = Field(pattern=r"^\d{4}$")
