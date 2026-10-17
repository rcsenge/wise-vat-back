"""API contracts for the exchange rates."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class RatesTable(BaseModel):
    """One unit of the base currency buys the listed amount of each currency."""

    base: str
    as_of: date
    source: str  # "demo cache" until the live Wise rates replace the table
    rates: dict[str, Decimal]


class Rate(BaseModel):
    source: str
    target: str
    rate: Decimal
