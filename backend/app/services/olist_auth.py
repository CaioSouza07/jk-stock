"""OAuth 2.0 (Authorization Code) with Olist ERP: login URL, code exchange and token refresh."""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from http import HTTPStatus
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.core.exceptions import AppError, MissingConfiguration
from app.services.token_store import OAuthTokens, TokenStore

logger = logging.getLogger(__name__)

SESSION_EXPIRED_MESSAGE = "Sessão do Olist expirada. Acesse /auth/login para conectar novamente."
REFRESH_REJECTED_STATUSES = (HTTPStatus.BAD_REQUEST, HTTPStatus.UNAUTHORIZED)


class OlistAuthError(AppError):
    status_code = HTTPStatus.BAD_GATEWAY
    message = "Falha na autenticação com o Olist."


class OlistNotConnected(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    message = "Olist não conectado. Acesse /auth/login para conectar."


class InvalidOAuthState(AppError):
    message = "Login expirado ou inválido. Inicie novamente em /auth/login."


def _utcnow() -> datetime:
    return datetime.now(UTC)


class OlistAuth:
    def __init__(
        self,
        settings: Settings,
        http: httpx.AsyncClient,
        store: TokenStore,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._settings = settings
        self._http = http
        self._store = store
        self._now = now
        # Serializes refreshes: the refresh token is single-use
        self._lock = asyncio.Lock()

    def ensure_configured(self) -> None:
        if not (
            self._settings.olist_client_id and self._settings.olist_client_secret.get_secret_value()
        ):
            raise MissingConfiguration(
                "OLIST_CLIENT_ID e OLIST_CLIENT_SECRET não configurados no servidor."
            )

    def authorization_url(self, state: str) -> str:
        params = {
            "client_id": self._settings.olist_client_id,
            "redirect_uri": self._settings.olist_redirect_uri,
            "scope": "openid",
            "response_type": "code",
            "state": state,
        }
        return f"{self._settings.olist_auth_url}?{urlencode(params)}"

    def current_tokens(self) -> OAuthTokens | None:
        return self._store.load()

    def is_connected(self, tokens: OAuthTokens | None) -> bool:
        return tokens is not None and not tokens.refresh_expired(self._now())

    async def exchange_code(self, code: str) -> OAuthTokens:
        tokens = await self._request_tokens(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._settings.olist_redirect_uri,
            }
        )
        async with self._lock:
            self._store.save(tokens)
        logger.info("Olist connected; access token valid until %s", tokens.access_expires_at)
        return tokens

    async def get_access_token(self) -> str:
        """Valid access token, refreshing it if needed. Raises OlistNotConnected."""
        tokens = self._store.load()
        if tokens is None:
            raise OlistNotConnected()
        if not tokens.access_expired(self._now()):
            return tokens.access_token

        async with self._lock:
            # Another request may have refreshed while we waited for the lock
            tokens = self._store.load()
            if tokens is None:
                raise OlistNotConnected()
            if tokens.access_expired(self._now()):
                tokens = await self._refresh(tokens)
            return tokens.access_token

    async def refresh_access_token(self, rejected_token: str) -> str:
        """Called after Olist answers 401: refresh unless another request already did."""
        async with self._lock:
            tokens = self._store.load()
            if tokens is None:
                raise OlistNotConnected()
            if tokens.access_token == rejected_token:
                tokens = await self._refresh(tokens)
            return tokens.access_token

    async def refresh_if_connected(self) -> None:
        """Scheduled job: keeps the refresh token alive. Never raises."""
        try:
            async with self._lock:
                tokens = self._store.load()
                if tokens is None:
                    logger.info("Skipping token refresh: Olist not connected")
                    return
                await self._refresh(tokens)
        except AppError as exc:
            logger.warning("Scheduled token refresh failed: %s", exc.message)
        except Exception:
            logger.exception("Scheduled token refresh failed")

    async def _refresh(self, tokens: OAuthTokens) -> OAuthTokens:
        """Caller must hold self._lock."""
        if tokens.refresh_expired(self._now()):
            raise OlistNotConnected(SESSION_EXPIRED_MESSAGE)
        new_tokens = await self._request_tokens(
            {"grant_type": "refresh_token", "refresh_token": tokens.refresh_token},
            is_refresh=True,
        )
        self._store.save(new_tokens)
        logger.info("Olist token refreshed; valid until %s", new_tokens.access_expires_at)
        return new_tokens

    async def _request_tokens(
        self, data: dict[str, str], *, is_refresh: bool = False
    ) -> OAuthTokens:
        self.ensure_configured()
        payload = {
            **data,
            "client_id": self._settings.olist_client_id,
            "client_secret": self._settings.olist_client_secret.get_secret_value(),
        }
        now = self._now()
        try:
            response = await self._http.post(self._settings.olist_token_url, data=payload)
        except httpx.HTTPError as exc:
            logger.warning("Olist token request failed: %r", exc)
            raise OlistAuthError("Não foi possível conectar ao Olist.") from exc

        if response.status_code != HTTPStatus.OK:
            logger.warning(
                "Olist token endpoint returned %s: %s", response.status_code, response.text[:500]
            )
            # 400 invalid_grant: refresh token expired or already used
            if is_refresh and response.status_code in REFRESH_REJECTED_STATUSES:
                raise OlistNotConnected(SESSION_EXPIRED_MESSAGE)
            raise OlistAuthError()

        try:
            return OAuthTokens.from_token_response(response.json(), now)
        except (ValueError, KeyError, TypeError) as exc:
            raise OlistAuthError("Resposta inválida do Olist ao obter o token.") from exc
