"""Money value type. Always Decimal, never float."""
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# Decimals used when rounding; anything not listed has 2.
# HUF is 2 in ISO 4217, but forint amounts are shown and claimed in whole forints.
MINOR_UNITS = {"HUF": 0, "JPY": 0}

_CURRENCY = re.compile(r"^[A-Z]{3}$")


def quantize(amount: Decimal, currency: str) -> Decimal:
    exponent = Decimal(1).scaleb(-MINOR_UNITS.get(currency, 2))
    return amount.quantize(exponent, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str  # ISO 4217, e.g. "HUF", "EUR"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError(f"Money amount must be Decimal, got {type(self.amount).__name__}")
        if not _CURRENCY.match(self.currency):
            raise ValueError(f"Invalid ISO 4217 currency: {self.currency!r}")

    @classmethod
    def zero(cls, currency: str) -> "Money":
        return cls(Decimal(0), currency)

    def _same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")

    def __add__(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __radd__(self, other: object) -> "Money":
        # Lets sum() work: sum(items) starts from the int 0.
        if other == 0:
            return self
        return NotImplemented

    def __sub__(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def rounded(self) -> "Money":
        return Money(quantize(self.amount, self.currency), self.currency)

    def convert(self, target: str, rate: Decimal) -> "Money":
        """rate = units of target per 1 unit of self.currency (e.g. EUR->HUF 395.12)."""
        if not isinstance(rate, Decimal):
            raise TypeError(f"Rate must be Decimal, got {type(rate).__name__}")
        if rate <= 0:
            raise ValueError(f"Rate must be positive, got {rate}")
        return Money(quantize(self.amount * rate, target), target)
