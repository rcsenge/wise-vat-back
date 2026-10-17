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
    assert claims["deadlines"] == []
    expired = {total["country"]: Decimal(total["refundable_vat_total"]) for total in claims["expired_per_country"]}
    assert expired == {"AT": Decimal("26.00")}


def test_deadline_day_is_still_claimable(client, monkeypatch):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    monkeypatch.setattr(settings, "claim_reference_date", date(2027, 9, 30))
    assert client.get("/receipts").json()[0]["expired"] is False
    assert client.get("/claims").json()["per_country"][0]["country"] == "AT"


def test_claims_list_the_deadline_per_country(client):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    client.post("/invoices", json=load_invoice("de_hotel_munich.json"))
    deadlines = client.get("/claims").json()["deadlines"]
    assert [(item["country"], item["claim_deadline"], Decimal(item["refundable_vat_total"])) for item in deadlines] == [
        ("AT", "2027-09-30", Decimal("26.00")),
        ("DE", "2027-09-30", Decimal("10.50")),
    ]
    assert client.get("/claims").json()["expired_per_country"] == []
