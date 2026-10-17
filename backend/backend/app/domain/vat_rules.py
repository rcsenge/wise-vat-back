"""VAT back rules for the supported countries. Pure. No I/O.

The rules map an expense category to an eligibility decision per country.
The supported countries are Austria (AT) and Germany (DE).
A decision carries a human-readable reason for the UI and the pitch.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Country = Literal["AT", "DE"]
SUPPORTED_COUNTRIES: frozenset[str] = frozenset({"AT", "DE"})

# The ten expense categories of Directive 2008/9/EC, Art. 9.
CATEGORIES: tuple[str, ...] = (
    "FUEL",
    "VEHICLE_HIRE",
    "VEHICLE_EXPENSES",
    "ROAD_TOLL",
    "TRAVEL",
    "ACCOMMODATION",
    "FOOD_AND_DRINK",
    "FAIR_ADMISSION",
    "ENTERTAINMENT",
    "OTHER",
)


@dataclass(frozen=True)
class CategoryRule:
    eligible: bool
    reason: str


@dataclass(frozen=True)
class LineDecision:
    line_index: int
    category: str
    eligible: bool
    refundable_vat: Decimal
    reason: str


# Base rule: every business category is refundable except entertainment.
def _default_rules(country: str) -> dict[str, CategoryRule]:
    rules: dict[str, CategoryRule] = {}
    for category in CATEGORIES:
        if category == "ENTERTAINMENT":
            rules[category] = CategoryRule(
                False, f"Entertainment expenses are not refundable in {country}."
            )
        else:
            rules[category] = CategoryRule(
                True, f"Refundable business expense under Directive 2008/9/EC in {country}."
            )
    return rules


COUNTRY_RULES: dict[str, dict[str, CategoryRule]] = {
    "AT": _default_rules("Austria"),
    "DE": _default_rules("Germany"),
}


def is_supported(country: str) -> bool:
    return country in SUPPORTED_COUNTRIES


def evaluate_line(country: str, category: str, line_index: int, vat_amount: Decimal) -> LineDecision:
    """Return the decision for one invoice line."""
    if country not in COUNTRY_RULES:
        raise ValueError(f"Unsupported country: {country}")
    rule = COUNTRY_RULES[country].get(category)
    if rule is None:
        rule = CategoryRule(False, f"No rule for category {category} in {country}.")
    refundable = vat_amount if rule.eligible else Decimal("0")
    return LineDecision(
        line_index=line_index,
        category=category,
        eligible=rule.eligible,
        refundable_vat=refundable,
        reason=rule.reason,
    )
