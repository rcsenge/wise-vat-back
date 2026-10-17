"""The claim deadline in the invoice flow, the receipts list and the claims summary."""
from datetime import date
from decimal import Decimal

from app.config import settings
from tests.helpers import load_invoice


def test_invoice_after_the_deadline_is_rejected(client):
    data = load_invoice("at_hotel_vienna.json")
    data["issueDate"] = "2025-09-17"
    body = client.post("/invoices", json=data).json()
    assert body["status"] == "rejected"
    assert body["reasons"] == [
        "The refund deadline for 2025 invoices passed on 30 September 2026. The VAT cannot be claimed any more."
    ]


def test_stored_invoice_expires_when_the_deadline_passes(client, monkeypatch):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    monkeypatch.setattr(settings, "claim_reference_date", date(2027, 10, 1))

    receipt = client.get("/receipts").json()[0]
    assert receipt["status"] == "approved"
    assert receipt["expired"] is True
    assert receipt["reasons"][0].startswith("The refund deadline for 2026 invoices passed on 30 September 2027.")

    claims = client.get("/claims").json()
    assert claims["per_country"] == []
    assert claims["periods"] == []
    assert claims["reference_date"] == "2027-10-01"
    expired = {total["country"]: Decimal(total["refundable_vat_total"]) for total in claims["expired_per_country"]}
    assert expired == {"AT": Decimal("26.00")}


def test_deadline_day_is_still_claimable(client, monkeypatch):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    monkeypatch.setattr(settings, "claim_reference_date", date(2027, 9, 30))
    assert client.get("/receipts").json()[0]["expired"] is False
    assert client.get("/claims").json()["per_country"][0]["country"] == "AT"


def test_claims_list_one_period_per_country_and_year(client):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    client.post("/invoices", json=load_invoice("de_hotel_munich.json"))
    claims = client.get("/claims").json()
    periods = [
        (item["country"], item["year"], item["period_start"], item["claim_deadline"], Decimal(item["refundable_vat_total"]), item["invoice_count"])
        for item in claims["periods"]
    ]
    assert periods == [
        ("AT", 2026, "2026-01-01", "2027-09-30", Decimal("26.00"), 1),
        ("DE", 2026, "2026-01-01", "2027-09-30", Decimal("10.50"), 1),
    ]
    assert claims["expired_per_country"] == []
    assert claims["reference_date"] == "2026-10-17"


def store_approved(engine, issue_date: date, amount: str) -> None:
    from sqlmodel import Session

    from app.models.invoice_record import InvoiceRecord
    from app.schemas.invoice_flow import CountryTotal, InvoiceResult

    result = InvoiceResult(
        status="approved",
        invoice_number=f"INV-{issue_date.isoformat()}",
        country_totals=[CountryTotal(country="AT", currency="EUR", refundable_vat_total=Decimal(amount))],
    )
    with Session(engine) as session:
        session.add(
            InvoiceRecord(
                status="approved",
                invoice_number=result.invoice_number,
                issue_date=issue_date,
                merchant="Hotel",
                currency="EUR",
                gross_amount=Decimal("100"),
                refundable_vat=Decimal(amount),
                country="AT",
                result_json=result.model_dump_json(),
            )
        )
        session.commit()


def test_each_year_has_its_own_period_and_deadline(client, engine, monkeypatch):
    store_approved(engine, date(2025, 11, 10), "12.00")
    store_approved(engine, date(2026, 3, 2), "30.00")

    # In June 2026 both years are open. Each has its own money and deadline.
    monkeypatch.setattr(settings, "claim_reference_date", date(2026, 6, 1))
    periods = [(item["year"], item["claim_deadline"], Decimal(item["refundable_vat_total"])) for item in client.get("/claims").json()["periods"]]
    assert periods == [(2025, "2026-09-30", Decimal("12.00")), (2026, "2027-09-30", Decimal("30.00"))]

    # After 30 September 2026 the 2025 period closes. Its money leaves the open total.
    monkeypatch.setattr(settings, "claim_reference_date", date(2026, 10, 1))
    claims = client.get("/claims").json()
    assert [item["year"] for item in claims["periods"]] == [2026]
    assert Decimal(claims["per_country"][0]["refundable_vat_total"]) == Decimal("30.00")
    assert Decimal(claims["expired_per_country"][0]["refundable_vat_total"]) == Decimal("12.00")
