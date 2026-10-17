"""App settings, read from environment / .env (see ../.env.example)."""
from datetime import date
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    wise_mode: Literal["mock", "sandbox", "real"] = "mock"
    wise_api_token: str = ""
    wise_sandbox_url: str = "https://api.sandbox.transferwise.tech"
    wise_real_url: str = "https://api.transferwise.com"

    # "demo" returns the Berlin hotel invoice for every upload after the delay. "ollama" reads the document with the AI.
    invoice_reader: Literal["demo", "ollama"] = "demo"
    demo_reader_delay_seconds: float = 3.0

    # The local Ollama server reads invoice PDFs and photos. It needs no API key.
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5vl:7b"
    ollama_timeout_seconds: float = 300.0

    # The claim deadline check uses this date as today. Empty means the real date.
    # Tests fix it. A demo can set a future date to show expired invoices.
    claim_reference_date: date | None = None

    # The applicant of the refund application. The claim package prints these values.
    applicant_name: str = "Példa Tech Kft."
    applicant_vat_number: str = "HU12345678"
    applicant_address: str = "Váci út 45, 1134 Budapest, Hungary"
    applicant_email: str = "finance@peldatech.example"
    applicant_iban: str = "HU42 1177 3016 1111 1018 0000 0000"
    applicant_bic: str = "OTPVHUHB"
    applicant_activity: str = "Software development (NACE 62.01)"
    applicant_establishment_country: str = "HU"
    applicant_establishment_portal: str = "the NAV online portal (Hungary)"

    database_url: str = "sqlite:///./vatback.db"
    cors_origins: str = "http://localhost:8080"
    # The regex allows any host on the frontend port. A phone opens the frontend by LAN IP.
    cors_origin_regex: str = r"^https?://[^/:]+:8080$"


settings = Settings()
