"""CORS tests. A phone on the LAN must reach the API by IP address."""
import pytest
from fastapi.testclient import TestClient


def preflight(client: TestClient, origin: str) -> str | None:
    response = client.options(
        "/receipts",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )
    return response.headers.get("access-control-allow-origin")


@pytest.mark.parametrize(
    "origin",
    ["http://localhost:8080", "http://localhost:5173", "http://192.168.1.23:8080", "http://152.66.169.164:8080"],
)
def test_frontend_origin_is_allowed(client: TestClient, origin: str) -> None:
    assert preflight(client, origin) == origin


@pytest.mark.parametrize("origin", ["http://evil.example.com", "http://192.168.1.23:9000", "http://a.com:8080.evil.com"])
def test_other_origin_is_rejected(client: TestClient, origin: str) -> None:
    assert preflight(client, origin) is None
