"""Picks the WiseClient implementation based on WISE_MODE."""
from functools import lru_cache

from app.config import settings
from app.integrations.wise_client import WiseClient
from app.integrations.wise_mock import MockWiseClient
from app.integrations.wise_real import RealWiseClient


@lru_cache
def get_wise_client() -> WiseClient:
    if settings.wise_mode == "mock":
        return MockWiseClient()
    base_url = settings.wise_sandbox_url if settings.wise_mode == "sandbox" else settings.wise_real_url
    return RealWiseClient(base_url, settings.wise_api_token)
