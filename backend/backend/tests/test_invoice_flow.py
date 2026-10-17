"""Invoice flow through the API: approve, reject paths, and claims summary."""
from decimal import Decimal

from tests.helpers import load_invoice


def test_at_hotel_approved(client):
    response = client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "approved"
    assert body["matched_transaction"]["country"] == "AT"
    assert len(body["country_totals"]) == 1
    assert Decimal(body["country_totals"][0]["refundable_vat_total"]) == Decimal("26.00")
    assert len([line for line in body["line_outcomes"] if line["eligible"]]) == 3


def test_de_taxi_rejected_missing_vat(client):
    response = client.post("/invoices", json=load_invoice("de_taxi_receipt_no_vat_id.json"))
    body = response.json()
    assert body["status"] == "rejected"
    assert any("VAT number" in reason for reason in body["reasons"])


def test_pl_restaurant_rejected_by_country_rule(client):
    response = client.post("/invoices", json=load_invoice("pl_restaurant_warsaw.json"))
    body = response.json()
    assert body["status"] == "rejected"
    assert body["matched_transaction"]["country"] == "PL"
    assert body["reasons"] == ["No invoice line is eligible for VAT back."]
    assert all("restaurant services" in line["reason"] for line in body["line_outcomes"])
    assert all(Decimal(line["refundable_vat"]) == Decimal("0") for line in body["line_outcomes"])


def test_unsupported_country_is_rejected(client):
    data = load_invoice("pl_restaurant_warsaw.json")
    data["currency"] = "GBP"
    data["supplier"]["address"]["countryCode"] = "GB"
    data["totals"]["grossAmount"] = "120.00"
    response = client.post("/invoices", json=data)
    body = response.json()
    assert body["status"] == "rejected"
    assert any("not supported" in reason for reason in body["reasons"])


def test_de_hotel_approved(client):
    response = client.post("/invoices", json=load_invoice("de_hotel_munich.json"))
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "approved"
    assert body["matched_transaction"]["country"] == "DE"
    assert Decimal(body["country_totals"][0]["refundable_vat_total"]) == Decimal("10.50")
    assert len([line for line in body["line_outcomes"] if line["eligible"]]) == 1


def test_unknown_vat_number_is_rejected(client):
    data = load_invoice("at_hotel_vienna.json")
    data["supplier"]["vatNumber"] = "XX12345678"
    response = client.post("/invoices", json=data)
    body = response.json()
    assert body["status"] == "rejected"
    assert any("not valid" in reason for reason in body["reasons"])


def test_no_matching_transaction_is_rejected(client):
    data = load_invoice("at_hotel_vienna.json")
    data["totals"]["grossAmount"] = "999.99"
    response = client.post("/invoices", json=data)
    body = response.json()
    assert body["status"] == "rejected"
    assert any("No matching" in reason for reason in body["reasons"])


def test_claims_summary_per_country(client, stored_seed_invoices):
    response = client.get("/claims")
    body = response.json()
    assert response.status_code == 200
    countries = {total["country"] for total in body["per_country"]}
    assert countries == {"AT", "DE"}
    assert len(body["results"]) == 4
    totals = {total["country"]: Decimal(total["refundable_vat_total"]) for total in body["per_country"]}
    assert totals == {"AT": Decimal("26.00"), "DE": Decimal("10.50")}


def test_receipts_list_frontend_shape(client):
    data = load_invoice("at_hotel_vienna.json")
    data["imageDataUrl"] = "data:image/jpeg;base64,AAAA"
    client.post("/invoices", json=data)
    response = client.get("/receipts")
    receipts = response.json()
    assert response.status_code == 200
    assert len(receipts) == 1
    receipt = receipts[0]
    assert set(receipt) == {"id", "merchant", "amount", "taxAmount", "currency", "country", "scannedAt", "imageDataUrl", "status", "reasons"}
    assert isinstance(receipt["id"], str)
    assert isinstance(receipt["scannedAt"], int)
    assert receipt["imageDataUrl"] == "data:image/jpeg;base64,AAAA"
    assert receipt["status"] == "approved"
    assert receipt["country"] == "AT"
    assert Decimal(receipt["amount"]) == Decimal("261.00")
    assert Decimal(receipt["taxAmount"]) == Decimal("26.00")


def test_rejected_invoice_is_listed(client):
    client.post("/invoices", json=load_invoice("de_taxi_receipt_no_vat_id.json"))
    receipt = client.get("/receipts").json()[0]
    assert receipt["status"] == "rejected"
    assert Decimal(receipt["taxAmount"]) == Decimal("0")
    assert receipt["imageDataUrl"] is None
    assert any("VAT number" in reason for reason in receipt["reasons"])


def test_receipts_newest_first(client):
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    client.post("/invoices", json=load_invoice("de_hotel_munich.json"))
    merchants = [receipt["merchant"] for receipt in client.get("/receipts").json()]
    assert merchants[0] != merchants[1]
    assert merchants[0] == load_invoice("de_hotel_munich.json")["supplier"]["name"]


def test_same_invoice_twice_is_rejected(client):
    first = client.post("/invoices", json=load_invoice("at_hotel_vienna.json")).json()
    second = client.post("/invoices", json=load_invoice("at_hotel_vienna.json")).json()
    assert first["status"] == "approved"
    assert second["status"] == "rejected"
    assert any("unclaimed" in reason for reason in second["reasons"])


def test_submitted_invoice_adds_to_claims(client):
    assert client.get("/claims").json()["per_country"] == []
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    per_country = client.get("/claims").json()["per_country"]
    assert [(total["country"], Decimal(total["refundable_vat_total"])) for total in per_country] == [("AT", Decimal("26.00"))]


def test_seed_invoices_keep_non_ascii_names():
    from app.services.invoice_flow import iter_seed_invoices

    names = {invoice.supplier.name for invoice in iter_seed_invoices()}
    assert "Hotel München Mitte GmbH" in names


def test_transaction_in_other_country_is_not_matched(client):
    data = load_invoice("at_hotel_vienna.json")
    data["supplier"]["address"]["countryCode"] = "DE"
    body = client.post("/invoices", json=data).json()
    assert body["status"] == "rejected"
    assert any("No matching" in reason for reason in body["reasons"])


def test_transaction_outside_date_window_is_not_matched(client):
    data = load_invoice("at_hotel_vienna.json")
    data["issueDate"] = "2026-06-01"
    body = client.post("/invoices", json=data).json()
    assert body["status"] == "rejected"
    assert any("No matching" in reason for reason in body["reasons"])


def test_transaction_a_few_days_off_is_matched(client):
    data = load_invoice("at_hotel_vienna.json")
    data["issueDate"] = "2026-09-20"
    body = client.post("/invoices", json=data).json()
    assert body["status"] == "approved"


def test_closest_transaction_date_wins(client, engine):
    from datetime import date

    from sqlmodel import Session

    from app.models.transaction import Transaction
    from seed.seed import paid_on

    with Session(engine) as session:
        closer = Transaction(account_id=1, amount=Decimal("261.00"), currency="EUR", country="AT", merchant="Hotel Ringstrasse GmbH", kind="card", created_at=paid_on(date(2026, 9, 25)))
        session.add(closer)
        session.commit()
        closer_id = closer.id
    data = load_invoice("at_hotel_vienna.json")
    data["issueDate"] = "2026-09-24"
    body = client.post("/invoices", json=data).json()
    assert body["matched_transaction"]["transaction_id"] == closer_id


def test_claims_sum_every_approved_invoice_beyond_the_result_limit(client, monkeypatch):
    from app.services import invoice_flow

    monkeypatch.setattr(invoice_flow, "MAX_CLAIM_RESULTS", 1)
    monkeypatch.setattr(invoice_flow, "CLAIM_BATCH_SIZE", 1)
    client.post("/invoices", json=load_invoice("at_hotel_vienna.json"))
    client.post("/invoices", json=load_invoice("de_hotel_munich.json"))
    client.post("/invoices", json=load_invoice("de_taxi_receipt_no_vat_id.json"))
    body = client.get("/claims").json()
    totals = {total["country"]: Decimal(total["refundable_vat_total"]) for total in body["per_country"]}
    assert totals == {"AT": Decimal("26.00"), "DE": Decimal("10.50")}
    assert [result["status"] for result in body["results"]] == ["rejected"]
