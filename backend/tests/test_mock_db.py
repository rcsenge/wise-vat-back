"""Mock database: every supported country gets receipts and a claim total."""
from datetime import date

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from app.domain import vat_rules
from app.services.invoice_flow import compute_claims, list_receipts
from seed.mock_db import MOCK_COUNTRIES, build_mock_database, generate_receipts

TODAY = date(2026, 10, 17)


def test_mock_receipts_are_identical_on_every_run():
    first = [receipt.invoice for receipt in generate_receipts(TODAY)]
    second = [receipt.invoice for receipt in generate_receipts(TODAY)]
    assert first == second


def test_mock_database_covers_every_supported_country():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    build_mock_database(engine, TODAY)

    with Session(engine) as session:
        receipts = list_receipts(session)
        claims = compute_claims(session)

    merchant_count = sum(len(country.merchants) for country in MOCK_COUNTRIES)
    defect_count = sum(1 for country in MOCK_COUNTRIES for merchant in country.merchants if merchant.defect)
    assert {country.code for country in MOCK_COUNTRIES} == vat_rules.SUPPORTED_COUNTRIES
    assert len(receipts) == merchant_count
    assert {total.country for total in claims.per_country} == vat_rules.SUPPORTED_COUNTRIES
    assert [receipt.scanned_at for receipt in receipts] == sorted((receipt.scanned_at for receipt in receipts), reverse=True)
    assert sum(1 for receipt in receipts if receipt.status == "rejected") >= defect_count
