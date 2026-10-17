"""Mock database: every supported country gets receipts and a claim total."""
from datetime import date

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from app.domain import vat_rules
from app.schemas.invoice_flow import InvoiceSubmission
from app.services.invoice_flow import compute_claims, list_receipts, submit_invoice
from seed.mock_db import MOCK_COUNTRIES, build_mock_database, generate_receipts, reset_printed_invoice

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
    # The printed demo invoice has no receipt. The demo uploads it.
    assert len(receipts) == merchant_count - 1
    assert {total.country for total in claims.per_country} == vat_rules.SUPPORTED_COUNTRIES
    assert [receipt.scanned_at for receipt in receipts] == sorted((receipt.scanned_at for receipt in receipts), reverse=True)
    assert sum(1 for receipt in receipts if receipt.status == "rejected") >= defect_count


# The values of the printed Fiera Milano PDF.
PRINTED_INVOICE = {
    "schemaVersion": "1.0",
    "documentType": "FULL_INVOICE",
    "invoiceNumber": "IT-MOCK-0019",
    "issueDate": "2026-10-07",
    "currency": "EUR",
    "supplier": {
        "name": "Fiera Milano S.p.A.",
        "vatNumber": "IT36957931860",
        "address": {"street": None, "postalCode": None, "city": "Milano", "countryCode": "IT"},
    },
    "customer": {"name": "Példa Tech Kft.", "vatNumber": "HU12345678"},
    "lines": [
        {
            "description": "Biglietto fiera",
            "category": "FAIR_ADMISSION",
            "netAmount": "360.53",
            "vatRate": 22.0,
            "vatAmount": "79.32",
            "grossAmount": "439.85",
        }
    ],
    "totals": {"netAmount": "360.53", "vatAmount": "79.32", "grossAmount": "439.85"},
    "cardLast4": "4821",
}


def test_printed_invoice_matches_again_after_reset():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    build_mock_database(engine, TODAY)
    submission = InvoiceSubmission.model_validate(PRINTED_INVOICE)

    with Session(engine) as session:
        first = submit_invoice(session, submission)
        session.commit()
        duplicate = submit_invoice(session, submission)
        session.commit()
    reset_printed_invoice(engine)
    with Session(engine) as session:
        again = submit_invoice(session, submission)

    assert first.status == "approved"
    assert duplicate.status == "rejected"
    assert again.status == "approved"
    assert again.matched_transaction == first.matched_transaction
