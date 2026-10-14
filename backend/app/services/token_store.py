"""Persistence of the Olist OAuth tokens: Upstash Redis in production, JSON file locally."""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from http import HTTPStatus
from pathlib import Path
from typing import Any, Protocol

import httpx

from app.core.config import Settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

DEFAULT_ACCESS_TTL_SECONDS = 4 * 3600
DEFAULT_REFRESH_TTL_SECONDS = 24 * 3600
EXPIRY_MARGIN = timedelta(minutes=5)


class TokenStoreError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    message = "Não foi possível acessar o armazenamento dos tokens do Olist. Tente novamente."


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime

    @classmethod
    def from_token_response(cls, data: dict[str, Any], now: datetime) -> "OAuthTokens":
        access_ttl = int(data.get("expires_in") or DEFAULT_ACCESS_TTL_SECONDS)
        refresh_ttl = int(data.get("refresh_expires_in") or DEFAULT_REFRESH_TTL_SECONDS)
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            access_expires_at=now + timedelta(seconds=access_ttl),
            refresh_expires_at=now + timedelta(seconds=refresh_ttl),
        )

    def access_expired(self, now: datetime) -> bool:
        return now >= self.access_expires_at - EXPIRY_MARGIN

    def refresh_expired(self, now: datetime) -> bool:
        return now >= self.refresh_expires_at

    def to_dict(self) -> dict[str, str]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "access_expires_at": self.access_expires_at.isoformat(),
            "refresh_expires_at": self.refresh_expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "OAuthTokens":
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            access_expires_at=datetime.fromisoformat(data["access_expires_at"]),
            refresh_expires_at=datetime.fromisoformat(data["refresh_expires_at"]),
        )


class TokenStore(Protocol):
    async def load(self) -> OAuthTokens | None:
        """Stored tokens, or None when never connected (or unreadable)."""

    async def save(self, tokens: OAuthTokens) -> None: ...


class FileTokenStore:
    """Local development only: hosts with an ephemeral disk lose the file on restart."""

    def __init__(self, path: Path) -> None:
        self.path = path

    async def load(self) -> OAuthTokens | None:
        try:
            return OAuthTokens.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except FileNotFoundError:
            return None
        except (OSError, ValueError, KeyError, TypeError):
            logger.exception("Could not read tokens file %s", self.path)
            return None

    async def save(self, tokens: OAuthTokens) -> None:
        """Atomic write: a crash mid-write never leaves a truncated file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(tokens.to_dict(), indent=2), encoding="utf-8")
        os.replace(tmp, self.path)


class UpstashTokenStore:
    """Upstash Redis through its REST API (one JSON command per POST)."""

    def __init__(self, http: httpx.AsyncClient, url: str, token: str, key: str) -> None:
        self._http = http
        self._url = url.rstrip("/")
        self._token = token
        self._key = key

    async def load(self) -> OAuthTokens | None:
        raw = await self._command("GET", self._key)
        if raw is None:
            return None
        try:
            return OAuthTokens.from_dict(json.loads(raw))
        except (ValueError, KeyError, TypeError):
            logger.exception("Invalid tokens stored in Upstash key %s", self._key)
            return None

    async def save(self, tokens: OAuthTokens) -> None:
        await self._command("SET", self._key, json.dumps(tokens.to_dict()))

    async def _command(self, *args: str) -> Any:
        """Raises TokenStoreError: an Upstash outage must not look like "Olist not connected"."""
        try:
            response = await self._http.post(
                self._url, json=list(args), headers={"Authorization": f"Bearer {self._token}"}
            )
        except httpx.HTTPError as exc:
            logger.warning("Upstash %s failed: %r", args[0], exc)
            raise TokenStoreError() from exc

        try:
            data = response.json()
        except ValueError:
            data = None
        if not response.is_success or not isinstance(data, dict) or "error" in data:
            logger.warning(
                "Upstash %s returned %s: %s", args[0], response.status_code, response.text[:200]
            )
            raise TokenStoreError()
        return data.get("result")


def create_token_store(settings: Settings, http: httpx.AsyncClient) -> TokenStore:
    if settings.upstash_redis_rest_url:
        logger.info("Olist tokens stored in Upstash Redis (key %s)", settings.tokens_redis_key)
        return UpstashTokenStore(
            http,
            settings.upstash_redis_rest_url,
            settings.upstash_redis_rest_token.get_secret_value(),
            settings.tokens_redis_key,
        )
    logger.warning(
        "UPSTASH_REDIS_REST_URL not set: Olist tokens stored in %s (local development only)",
        settings.tokens_file,
    )
    return FileTokenStore(settings.tokens_file)
