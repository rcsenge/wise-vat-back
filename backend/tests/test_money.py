"""Money: Decimal-only, same-currency arithmetic, rounding per currency."""
from decimal import Decimal

import pytest

from app.domain.money import Money, quantize


def eur(amount: str) -> Money:
    return Money(Decimal(amount), "EUR")


def test_add_and_sub_same_currency():
    assert eur("10.50") + eur("2.25") == eur("12.75")
    assert eur("10.50") - eur("2.25") == eur("8.25")


def test_mixing_currencies_is_an_error():
    with pytest.raises(ValueError, match="Currency mismatch"):
        eur("1") + Money(Decimal("1"), "PLN")
    with pytest.raises(ValueError, match="Currency mismatch"):
        eur("1") - Money(Decimal("1"), "PLN")


def test_sum_works():
    assert sum([eur("18.00"), eur("3.00"), eur("5.00")]) == eur("26.00")


def test_zero():
    assert Money.zero("CZK") + Money(Decimal("12.40"), "CZK") == Money(Decimal("12.40"), "CZK")


def test_float_amount_rejected():
    with pytest.raises(TypeError):
        Money(0.1, "EUR")  # type: ignore[arg-type]


@pytest.mark.parametrize("currency", ["eur", "EURO", "", "E1R"])
def test_invalid_currency_rejected(currency: str):
    with pytest.raises(ValueError):
        Money(Decimal("1"), currency)


@pytest.mark.parametrize(
    "amount,currency,expected",
    [
        ("2.345", "EUR", "2.35"),   # half up, not banker's rounding
        ("2.344", "EUR", "2.34"),
        ("-2.345", "EUR", "-2.35"),
        ("1234.5", "HUF", "1235"),
        ("1234.49", "HUF", "1234"),
        ("10", "PLN", "10.00"),
    ],
)
def test_quantize(amount: str, currency: str, expected: str):
    assert str(quantize(Decimal(amount), currency)) == expected


def test_rounded_keeps_currency():
    assert eur("2.345").rounded() == eur("2.35")


def test_convert_eur_to_huf_whole_forints():
    assert eur("33.12").convert("HUF", Decimal("395.12")) == Money(Decimal("13086"), "HUF")


def test_convert_pln_to_eur_two_decimals():
    assert Money(Decimal("38.40"), "PLN").convert("EUR", Decimal("0.2345")) == eur("9.00")


def test_convert_rejects_float_and_non_positive_rate():
    with pytest.raises(TypeError):
        eur("1").convert("HUF", 395.12)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        eur("1").convert("HUF", Decimal("0"))
