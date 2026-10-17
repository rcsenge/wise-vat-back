"""Exchange rates from the cached demo table."""
from decimal import Decimal


def test_rates_table_has_the_claim_currencies(client):
    table = client.get("/rates/table").json()
    assert table["base"] == "EUR"
    assert table["source"] == "demo cache"
    assert {"EUR", "CZK", "DKK", "PLN", "SEK", "HUF"} <= set(table["rates"])
    assert Decimal(table["rates"]["EUR"]) == Decimal("1")


def test_cross_rate_goes_through_the_base(client):
    body = client.get("/rates", params={"source": "CZK", "target": "EUR"}).json()
    assert body["source"] == "CZK"
    assert Decimal(body["rate"]) == (Decimal("1") / Decimal("25.20")).quantize(Decimal("0.000001"))


def test_unknown_currency_gives_404(client):
    assert client.get("/rates", params={"source": "EUR", "target": "XYZ"}).status_code == 404


def test_bad_currency_code_is_rejected(client):
    assert client.get("/rates", params={"source": "eur", "target": "HUF"}).status_code == 422
