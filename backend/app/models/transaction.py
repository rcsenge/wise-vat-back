from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, SQLModel


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id")
    amount: Decimal = Field(max_digits=18, decimal_places=4)
    currency: str = Field(max_length=3)
    country: str = Field(max_length=2)  # ISO 3166-1 alpha-2, where the card was used
    merchant: str = ""
    kind: str  # e.g. "incoming", "card", "conversion"
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
