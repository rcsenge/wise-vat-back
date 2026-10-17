"""Fake events for the demo panel. Each should persist + run rules + publish to SSE."""
from typing import Any


def card_swipe(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO
    return {"ok": True, "todo": "card_swipe"}


def skip_time(days: int) -> dict[str, Any]:
    # TODO: advance simulated clock (e.g. towards the 30 September claim deadline)
    return {"ok": True, "todo": "skip_time", "days": days}


def reset() -> dict[str, Any]:
    # TODO: drop + reseed DB
    return {"ok": True, "todo": "reset"}
