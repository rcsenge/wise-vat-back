"""UNWIRED. The live flow never calls this module. See REPO-FINDINGS.md item 2.

Demo control panel endpoints. Also stands in for Wise webhooks.
"""
from fastapi import APIRouter

from app.simulator import events as sim

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("/card-swipe")
def card_swipe(payload: dict | None = None) -> dict:
    return sim.card_swipe(payload or {})


@router.post("/skip-time")
def skip_time(days: int = 7) -> dict:
    return sim.skip_time(days)


@router.post("/reset")
def reset() -> dict:
    return sim.reset()
