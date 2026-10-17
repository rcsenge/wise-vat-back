"""Domain events the rules engine reacts to."""
from dataclasses import dataclass
from datetime import datetime

from app.domain.money import Money


@dataclass(frozen=True)
class CardSwipe:
    account_id: int
    amount: Money
    merchant: str
    at: datetime


@dataclass(frozen=True)
class TimeSkipped:
    days: int
    at: datetime


Event = CardSwipe | TimeSkipped
