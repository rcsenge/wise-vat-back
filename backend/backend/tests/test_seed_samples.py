"""Sample invoices: every sample loads, matches a transaction, and gets the expected decision."""
from decimal import Decimal

from sqlmodel import Session

from app.services.invoice_flow import compute_claims, iter_seed_invoices, submit_invoice
from seed.seed import SAMPLE_INVOICES_DIR, sample_transactions


def test_samples_cover_many_countries_and_currencies(engine):
    samples = iter_seed_invoices(SAMPLE_INVOICES_DIR)
    with Session(engine) as session:
        account_ids = {sample.currency: 1 for sample in samples}
        for transaction in sample_transactions(samples, account_ids):
            session.add(transaction)
        session.commit()
        results = [submit_invoice(session, sample) for sample in samples]
        claims = compute_claims(session)

    statuses = [result.status for result in results]
    assert statuses.count("rejected") == 5
    assert statuses.count("approved") == len(samples) - 5
    refunds = {result.invoice_number: result.country_totals[0].refundable_vat_total for result in results if result.country_totals}
    rejected = {result.invoice_number for result in results if result.status == "rejected"}
    assert {"AT-2026-1000", "PL-2026-1555"} <= rejected
    assert refunds["PL-2026-1592"] == Decimal("36.80")
    assert refunds["FR-2026-1259"] == Decimal("3.60")
    assert {total.country for total in claims.per_country} == {"AT", "DE", "FR", "IT", "NL", "PL", "CZ", "DK", "SE"}
    assert {total.currency for total in claims.per_country} == {"EUR", "PLN", "CZK", "DKK", "SEK"}
