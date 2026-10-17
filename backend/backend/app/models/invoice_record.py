"""One stored result of the invoice flow. The receipts list and the claims read it."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, SQLModel


class InvoiceRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(max_length=16)  # "approved" or "rejected"
    invoice_number: str | None = None
    merchant: str = ""
    currency: str = Field(max_length=3)
    gross_amount: Decimal = Field(max_digits=18, decimal_places=4)
    refundable_vat: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    country: str | None = Field(default=None, max_length=2)  # Country of the matched transaction
    transaction_id: int | None = Field(default=None, foreign_key="transaction.id")
    image_data_url: str | None = None
    result_json: str  # The full InvoiceResult as JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
