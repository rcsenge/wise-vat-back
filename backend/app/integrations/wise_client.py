"""UNWIRED. The live flow never calls this module. See REPO-FINDINGS.md item 2.

WiseClient interface. Business logic depends on this, never on a concrete client.
"""
from decimal import Decimal
from typing import Any, Protocol


class WiseClient(Protocol):
    def get_rate(self, source: str, target: str) -> Decimal: ...

    def list_balances(self, profile_id: int) -> list[dict[str, Any]]: ...

    def create_quote(self, profile_id: int, source: str, target: str, amount: Decimal) -> dict[str, Any]: ...

    def create_transfer(self, quote_id: str, recipient_id: int, reference: str) -> dict[str, Any]: ...
