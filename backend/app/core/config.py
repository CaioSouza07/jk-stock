from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "JKSTOCK - DANFE Reader"
    log_level: str = "INFO"

    olist_client_id: str = ""
    olist_client_secret: SecretStr = SecretStr("")
    olist_redirect_uri: str = "http://localhost:8000/auth/callback"
    olist_auth_url: str = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth"
    olist_token_url: str = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"
    olist_api_url: str = "https://api.tiny.com.br/public-api/v3"
    # S = outgoing invoices (sales), E = incoming invoices (purchases)
    olist_invoice_type: str = "S"
    olist_rate_limit_retries: int = 3
    olist_rate_limit_backoff_seconds: float = 2.0
    olist_max_concurrency: int = 3
    product_cache_ttl_seconds: int = 3600

    app_password: SecretStr = SecretStr("")
    tokens_file: Path = BACKEND_DIR / "tokens.json"
    token_refresh_enabled: bool = True
    token_refresh_interval_minutes: int = 180
    http_timeout_seconds: float = 15.0
    # Frontend origins allowed by CORS, separated by ";" (e.g. "https://app.com;https://x.com")
    cors_origins: str = ""
    # Unset: secure cookies whenever OLIST_REDIRECT_URI is HTTPS (the cookie lives on that host)
    cookie_secure: bool | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(";") if o.strip()]

    @property
    def use_secure_cookies(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.olist_redirect_uri.lower().startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
