"""Exchange rates via the WiseClient (real rates endpoint works with a personal token)."""
from fastapi import APIRouter

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("")
def get_rate(source: str = "EUR", target: str = "HUF") -> dict:
    # TODO: get_wise_client().get_rate(source, target), fall back to seed/rates_cache.json
    return {"source": source, "target": target, "rate": None}
