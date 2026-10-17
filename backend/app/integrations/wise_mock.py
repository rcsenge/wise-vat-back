"""In-memory Wise mock for features unavailable in HU / offline demos."""
from decimal import Decimal
from typing import Any


class MockWiseClient:
    def get_rate(self, source: str, target: str) -> Decimal:
        # TODO: read from seed/rates_cache.json
        raise NotImplementedError

    def list_balances(self, profile_id: int) -> list[dict[str, Any]]:
        # TODO: canned multi-currency balances
        return []

    def create_quote(self, profile_id: int, source: str, target: str, amount: Decimal) -> dict[str, Any]:
        raise NotImplementedError

    def create_transfer(self, quote_id: str, recipient_id: int, reference: str) -> dict[str, Any]:
        raise NotImplementedError
