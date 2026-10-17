"""App settings, read from environment / .env (see ../.env.example)."""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    wise_mode: Literal["mock", "sandbox", "real"] = "mock"
    wise_api_token: str = ""
    wise_sandbox_url: str = "https://api.sandbox.transferwise.tech"
    wise_real_url: str = "https://api.transferwise.com"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"

    # The local Ollama server reads invoice PDFs and photos. It needs no API key.
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5vl:7b"
    ollama_timeout_seconds: float = 300.0

    database_url: str = "sqlite:///./vatback.db"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    # The regex allows any host on the frontend port. A phone opens the frontend by LAN IP.
    cors_origin_regex: str = r"^https?://[^/:]+:8080$"


settings = Settings()
