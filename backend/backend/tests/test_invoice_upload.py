"""Upload entry point tests. The frontend sends the invoice JSON as a file."""
import json
from decimal import Decimal

from tests.helpers import load_invoice

IMAGE_DATA_URL = "data:image/jpeg;base64,AAAA"


def upload(client, data: dict | str, filename: str = "invoice.json", content_type: str = "application/json", **form):
    content = data if isinstance(data, str) else json.dumps(data)
    return client.post("/invoices/upload", files={"document": (filename, content, content_type)}, data=form)


def test_json_upload_is_approved(client):
    response = upload(client, load_invoice("at_hotel_vienna.json"))
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "approved"
    assert Decimal(body["country_totals"][0]["refundable_vat_total"]) == Decimal("26.00")


def test_upload_stores_the_receipt_with_image(client):
    upload(client, load_invoice("at_hotel_vienna.json"), image_data_url=IMAGE_DATA_URL)
    receipts = client.get("/receipts").json()
    assert len(receipts) == 1
    assert receipts[0]["merchant"] == "Hotel Ringstrasse GmbH"
    assert receipts[0]["imageDataUrl"] == IMAGE_DATA_URL


def test_json_file_name_is_enough(client):
    response = upload(client, load_invoice("at_hotel_vienna.json"), content_type="application/octet-stream")
    assert response.json()["status"] == "approved"


def test_second_upload_of_same_invoice_is_rejected(client):
    upload(client, load_invoice("at_hotel_vienna.json"))
    body = upload(client, load_invoice("at_hotel_vienna.json")).json()
    assert body["status"] == "rejected"
    assert any("No matching" in reason for reason in body["reasons"])


def test_image_upload_is_not_supported_yet(client):
    response = upload(client, "not-json", filename="receipt.jpg", content_type="image/jpeg")
    assert response.status_code == 415
    assert response.json()["detail"]["reasons"]


def test_broken_json_is_rejected_with_reasons(client):
    response = upload(client, "{not json")
    assert response.status_code == 422
    assert response.json()["detail"]["reasons"]


def test_missing_field_is_reported(client):
    data = load_invoice("at_hotel_vienna.json")
    del data["totals"]
    response = upload(client, data)
    assert response.status_code == 422
    assert any("totals" in reason for reason in response.json()["detail"]["reasons"])
