"""VAT rules: supported countries, refundable share per category, line decisions."""
from decimal import Decimal

import pytest

from app.domain import vat_rules
from app.domain.money import Money

# One row per country rule: country, category, VAT on the line, expected refundable VAT.
COUNTRY_RULE_CASES: list[tuple[str, str, Decimal, Decimal]] = [
    ("AT", "FUEL", Decimal("17.00"), Decimal("0.00")),
    ("AT", "VEHICLE_HIRE", Decimal("20.00"), Decimal("0.00")),
    ("AT", "VEHICLE_EXPENSES", Decimal("5.00"), Decimal("0.00")),
    ("AT", "ENTERTAINMENT", Decimal("10.00"), Decimal("0.00")),
    ("DE", "ENTERTAINMENT", Decimal("10.00"), Decimal("0.00")),
    ("FR", "ACCOMMODATION", Decimal("48.00"), Decimal("0.00")),
    ("FR", "TRAVEL", Decimal("3.50"), Decimal("0.00")),
    ("FR", "FUEL", Decimal("10.00"), Decimal("8.00")),
    ("FR", "VEHICLE_HIRE", Decimal("30.00"), Decimal("0.00")),
    ("FR", "VEHICLE_EXPENSES", Decimal("6.00"), Decimal("0.00")),
    ("FR", "ENTERTAINMENT", Decimal("10.00"), Decimal("0.00")),
    ("IT", "FUEL", Decimal("22.00"), Decimal("8.80")),
    ("IT", "VEHICLE_HIRE", Decimal("44.00"), Decimal("17.60")),
    ("IT", "VEHICLE_EXPENSES", Decimal("5.28"), Decimal("2.11")),
    ("IT", "ROAD_TOLL", Decimal("4.40"), Decimal("1.76")),
    ("IT", "TRAVEL", Decimal("9.00"), Decimal("0.00")),
    ("IT", "ENTERTAINMENT", Decimal("10.00"), Decimal("0.00")),
    ("NL", "FOOD_AND_DRINK", Decimal("9.00"), Decimal("0.00")),
    ("NL", "ENTERTAINMENT", Decimal("21.00"), Decimal("0.00")),
    ("PL", "ACCOMMODATION", Decimal("78.40"), Decimal("0.00")),
    ("PL", "FOOD_AND_DRINK", Decimal("38.40"), Decimal("0.00")),
    ("PL", "FUEL", Decimal("73.60"), Decimal("36.80")),
    ("PL", "VEHICLE_HIRE", Decimal("46.00"), Decimal("23.00")),
    ("PL", "VEHICLE_EXPENSES", Decimal("23.01"), Decimal("11.51")),
    ("PL", "ROAD_TOLL", Decimal("4.60"), Decimal("2.30")),
    ("PL", "ENTERTAINMENT", Decimal("23.00"), Decimal("0.00")),
    ("CZ", "ENTERTAINMENT", Decimal("210.00"), Decimal("0.00")),
    ("DK", "FOOD_AND_DRINK", Decimal("100.00"), Decimal("25.00")),
    ("DK", "FUEL", Decimal("80.00"), Decimal("0.00")),
    ("DK", "VEHICLE_HIRE", Decimal("250.00"), Decimal("0.00")),
    ("DK", "VEHICLE_EXPENSES", Decimal("40.00"), Decimal("0.00")),
    ("DK", "ENTERTAINMENT", Decimal("160.00"), Decimal("0.00")),
    ("SE", "VEHICLE_HIRE", Decimal("250.00"), Decimal("125.00")),
    ("SE", "ENTERTAINMENT", Decimal("75.00"), Decimal("0.00")),
]


def test_supported_countries():
    assert vat_rules.is_supported("AT")
    assert vat_rules.is_supported("DE")
    assert vat_rules.is_supported("PL")
    assert not vat_rules.is_supported("GB")


@pytest.mark.parametrize(("country", "category", "vat_amount", "expected"), COUNTRY_RULE_CASES)
def test_country_rule(country: str, category: str, vat_amount: Decimal, expected: Decimal):
    decision = vat_rules.evaluate_line(country, category, 0, vat_amount, "EUR")
    assert decision.refundable_vat.amount == expected
    assert decision.refundable_vat.currency == "EUR"
    assert decision.eligible == (expected > 0)
    assert "Source:" in decision.reason


def test_every_country_has_a_rule_for_every_category():
    for country in vat_rules.SUPPORTED_COUNTRIES:
        assert set(vat_rules.COUNTRY_RULES[country]) == set(vat_rules.CATEGORIES)


def test_every_rule_has_a_reason_and_a_source():
    for rules in vat_rules.COUNTRY_RULES.values():
        for rule in rules.values():
            assert rule.reason
            assert rule.source


def test_unrestricted_category_is_fully_refundable():
    decision = vat_rules.evaluate_line("AT", "ACCOMMODATION", 0, Decimal("18.00"), "EUR")
    assert decision.eligible
    assert decision.refundable_share == Decimal("1")
    assert decision.refundable_vat == Money(Decimal("18.00"), "EUR")
    assert "Austria" in decision.reason


def test_partial_share_is_in_the_decision_and_reason():
    decision = vat_rules.evaluate_line("IT", "FUEL", 2, Decimal("22.00"), "EUR")
    assert decision.line_index == 2
    assert decision.refundable_share == Decimal("0.4")
    assert "40%" in decision.reason


def test_share_must_be_between_zero_and_one():
    with pytest.raises(ValueError):
        vat_rules.CategoryRule(Decimal("1.5"), "Too much.", "None.")
    with pytest.raises(ValueError):
        vat_rules.CategoryRule(Decimal("-0.1"), "Too little.", "None.")


def test_share_must_be_decimal():
    with pytest.raises(TypeError):
        vat_rules.CategoryRule(0.5, "Float share.", "None.")  # type: ignore[arg-type]


def test_unknown_category_is_not_eligible():
    decision = vat_rules.evaluate_line("DE", "MYSTERY", 1, Decimal("5.00"), "EUR")
    assert not decision.eligible
    assert decision.refundable_vat.amount == Decimal("0.00")


def test_unsupported_country_raises():
    with pytest.raises(ValueError):
        vat_rules.evaluate_line("GB", "FOOD_AND_DRINK", 0, Decimal("1"), "EUR")
