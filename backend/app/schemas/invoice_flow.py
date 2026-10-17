"""API contracts for the invoice processing and claims flow."""
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.invoice import ExtractedInvoice

InvoiceStatus = Literal["approved", "rejected"]

MAX_IMAGE_DATA_URL_LENGTH = 2_000_000


class LineOutcome(BaseModel):
    line_index: int
    description: str
    category: str
    eligible: bool
    refundable_vat: Decimal
    reason: str


class MatchedTransaction(BaseModel):
    transaction_id: int
    amount: Decimal
    currency: str
    country: str
    merchant: str


class CountryTotal(BaseModel):
    country: str
    currency: str
    refundable_vat_total: Decimal = Field(default=Decimal("0"))
    eligible_line_count: int = 0
    transaction_ids: list[int] = Field(default_factory=list)


class InvoiceResult(BaseModel):
    status: InvoiceStatus
    invoice_number: str | None
    reasons: list[str] = Field(default_factory=list)
    matched_transaction: MatchedTransaction | None = None
    line_outcomes: list[LineOutcome] = Field(default_factory=list)
    country_totals: list[CountryTotal] = Field(default_factory=list)


class ClaimDeadline(BaseModel):
    """Refundable VAT of one country that shares one claim deadline."""

    country: str
    currency: str
    claim_deadline: date
    refundable_vat_total: Decimal


class ClaimsSummary(BaseModel):
    per_country: list[CountryTotal] = Field(default_factory=list)  # Only invoices inside the deadline
    expired_per_country: list[CountryTotal] = Field(default_factory=list)  # Approved, but the deadline passed
    deadlines: list[ClaimDeadline] = Field(default_factory=list)  # Earliest deadline first
    results: list[InvoiceResult] = Field(default_factory=list)


class InvoiceSubmission(ExtractedInvoice):
    """The extracted invoice plus the optional receipt image as a data URL."""

    image_data_url: str | None = Field(default=None, max_length=MAX_IMAGE_DATA_URL_LENGTH)


class ReceiptView(BaseModel):
    """One stored invoice in the shape of the frontend receipt list."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    merchant: str
    amount: Decimal
    tax_amount: Decimal
    currency: str
    country: str | None  # Country of the matched transaction
    scanned_at: int  # Milliseconds since the Unix epoch
    image_data_url: str | None
    status: InvoiceStatus
    reasons: list[str] = Field(default_factory=list)
    issue_date: date | None = None
    claim_deadline: date | None = None
    expired: bool = False  # An approved invoice after its claim deadline
