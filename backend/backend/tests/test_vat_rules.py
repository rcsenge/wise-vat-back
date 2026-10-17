"""VAT rules: supported countries, eligibility per category, line decisions."""
from decimal import Decimal

import pytest

from app.domain import vat_rules


def test_supported_countries():
    assert vat_rules.is_supported("AT")
    assert vat_rules.is_supported("DE")
    assert not vat_rules.is_supported("PL")


def test_entertainment_is_not_eligible_in_at_or_de():
    for country in ("AT", "DE"):
        decision = vat_rules.evaluate_line(country, "ENTERTAINMENT", 0, Decimal("10.00"))
        assert not decision.eligible
        assert decision.refundable_vat == Decimal("0")


def test_accommodation_is_eligible_in_at():
    decision = vat_rules.evaluate_line("AT", "ACCOMMODATION", 0, Decimal("18.00"))
    assert decision.eligible
    assert decision.refundable_vat == Decimal("18.00")
    assert decision.reason


def test_unknown_category_is_not_eligible():
    decision = vat_rules.evaluate_line("DE", "MYSTERY", 1, Decimal("5.00"))
    assert not decision.eligible


def test_unsupported_country_raises():
    with pytest.raises(ValueError):
        vat_rules.evaluate_line("PL", "FOOD_AND_DRINK", 0, Decimal("1"))
