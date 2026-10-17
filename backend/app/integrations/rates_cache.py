"""The cached exchange rate table in seed/rates_cache.json. The mock Wise client reads it."""
import json
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from app.schemas.rates import RatesTable

RATES_CACHE_PATH = Path(__file__).resolve().parents[2] / "seed" / "rates_cache.json"
RATE_DECIMALS = Decimal("0.000001")


@lru_cache
def load_rates_table() -> RatesTable:
    data = json.loads(RATES_CACHE_PATH.read_text(encoding="utf-8"))
    return RatesTable.model_validate({key: value for key, value in data.items() if not key.startswith("_")})


def cross_rate(source: str, target: str) -> Decimal:
    """Return how much target currency one unit of source currency buys. Raise KeyError for an unknown currency."""
    table = load_rates_table()
    return (table.rates[target] / table.rates[source]).quantize(RATE_DECIMALS)
