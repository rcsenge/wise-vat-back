"""The refund claim deadline. Pure. No I/O.

Directive 2008/9/EC, Art. 15: a refund application must reach the Member State of
establishment by 30 September of the year after the refund period. The deadline is
preclusive (CJEU C-294/11, Elsacom). After it, the right to the refund is lost.
"""
from datetime import date

DEADLINE_MONTH = 9
DEADLINE_DAY = 30


def claim_deadline(issue_date: date) -> date:
    """Return the last day to claim the VAT of an invoice issued on issue_date."""
    return date(issue_date.year + 1, DEADLINE_MONTH, DEADLINE_DAY)


def is_expired(issue_date: date, today: date) -> bool:
    """Return True when the claim deadline of the invoice is in the past."""
    return today > claim_deadline(issue_date)


def expiry_reason(issue_date: date) -> str:
    """Return the human-readable reason for an expired invoice."""
    deadline = claim_deadline(issue_date)
    return (
        f"The refund deadline for {issue_date.year} invoices passed on "
        f"{deadline.day} {deadline:%B %Y}. The VAT cannot be claimed any more."
    )
