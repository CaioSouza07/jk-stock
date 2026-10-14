"""Persistence of the Olist OAuth tokens in a JSON file (kept out of git)."""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_ACCESS_TTL_SECONDS = 4 * 3600
DEFAULT_REFRESH_TTL_SECONDS = 24 * 3600
EXPIRY_MARGIN = timedelta(minutes=5)


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


class TokenStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> OAuthTokens | None:
        try:
            return OAuthTokens.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except FileNotFoundError:
            return None
        except (OSError, ValueError, KeyError, TypeError):
            logger.exception("Could not read tokens file %s", self.path)
            return None

    def save(self, tokens: OAuthTokens) -> None:
        """Atomic write: a crash mid-write never leaves a truncated file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(tokens.to_dict(), indent=2), encoding="utf-8")
        os.replace(tmp, self.path)
