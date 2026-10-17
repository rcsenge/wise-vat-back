"""UNWIRED. The live flow never calls this module. See REPO-FINDINGS.md item 2.

Real/sandbox Wise API client over httpx.
"""
from decimal import Decimal
from typing import Any

import httpx


class RealWiseClient:
    def __init__(self, base_url: str, token: str):
        self._http = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {token}"}, timeout=10)

    def get_rate(self, source: str, target: str) -> Decimal:
        # TODO (implement first): GET /v1/rates?source=..&target=.. -> Decimal(str(rate))
        raise NotImplementedError

    def list_balances(self, profile_id: int) -> list[dict[str, Any]]:
        # TODO: GET /v4/profiles/{profile_id}/balances?types=STANDARD
        raise NotImplementedError

    def create_quote(self, profile_id: int, source: str, target: str, amount: Decimal) -> dict[str, Any]:
        # TODO: POST /v3/profiles/{profile_id}/quotes
        raise NotImplementedError

    def create_transfer(self, quote_id: str, recipient_id: int, reference: str) -> dict[str, Any]:
        # TODO: POST /v1/transfers
        raise NotImplementedError
