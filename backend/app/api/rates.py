"""Exchange rates. The mock Wise client reads the cached table. The real client calls the Wise API."""
from fastapi import APIRouter, HTTPException, Query

from app.integrations.factory import get_wise_client
from app.integrations.rates_cache import load_rates_table
from app.schemas.rates import Rate, RatesTable

router = APIRouter(prefix="/rates", tags=["rates"])

CURRENCY_PATTERN = r"^[A-Z]{3}$"


@router.get("", response_model=Rate)
def get_rate(
    source: str = Query(default="EUR", pattern=CURRENCY_PATTERN),
    target: str = Query(default="HUF", pattern=CURRENCY_PATTERN),
) -> Rate:
    try:
        rate = get_wise_client().get_rate(source, target)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"reasons": [f"No rate for {source} to {target}."]}) from error
    return Rate(source=source, target=target, rate=rate)


@router.get("/table", response_model=RatesTable)
def get_rates_table() -> RatesTable:
    """Return the whole table. The employer page converts the totals into one currency with it."""
    return load_rates_table()
