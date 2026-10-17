"""Refund claim deadline: 30 September of the year after the invoice year."""
from datetime import date

import pytest

from app.domain.claim_deadline import claim_deadline, expiry_reason, is_expired


@pytest.mark.parametrize(
    ("issue_date", "deadline"),
    [
        (date(2026, 1, 5), date(2027, 9, 30)),
        (date(2026, 12, 31), date(2027, 9, 30)),
        (date(2025, 11, 10), date(2026, 9, 30)),
    ],
)
def test_deadline_is_30_september_of_the_next_year(issue_date, deadline):
    assert claim_deadline(issue_date) == deadline


def test_the_deadline_day_itself_is_still_open():
    assert not is_expired(date(2025, 3, 1), today=date(2026, 9, 30))


def test_the_day_after_the_deadline_is_expired():
    assert is_expired(date(2025, 3, 1), today=date(2026, 10, 1))


def test_a_january_invoice_stays_open_for_more_than_a_year():
    assert not is_expired(date(2026, 1, 5), today=date(2027, 6, 1))


def test_expiry_reason_names_the_year_and_the_date():
    assert expiry_reason(date(2025, 11, 10)) == (
        "The refund deadline for 2025 invoices passed on 30 September 2026. The VAT cannot be claimed any more."
    )
