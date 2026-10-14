"""Olist ERP API v3 client: bearer auth, 401 refresh, 429 retries and product cache."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.olist_auth import OlistAuth

logger = logging.getLogger(__name__)

MAX_RETRY_WAIT_SECONDS = 30.0


class OlistApiError(AppError):
    status_code = HTTPStatus.BAD_GATEWAY
    message = "Erro ao consultar o Olist. Tente novamente."


class OlistRateLimited(OlistApiError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    message = "Limite de requisições do Olist atingido. Tente novamente em instantes."


class OlistForbidden(OlistApiError):
    message = (
        "Acesso negado pelo Olist. Verifique se o usuário conectado tem permissão "
        "nos módulos de notas fiscais e produtos."
    )


class OlistClient:
    def __init__(
        self,
        settings: Settings,
        http: httpx.AsyncClient,
        auth: OlistAuth,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._http = http
        self._auth = auth
        self._sleep = sleep
        self._clock = clock
        self._product_cache: dict[int, tuple[float, dict[str, Any]]] = {}

    async def find_invoices(self, number: int) -> list[dict[str, Any]]:
        params = {"numero": number, "tipo": self._settings.olist_invoice_type, "limit": 100}
        data = await self._get("/notas", params=params)
        return (data or {}).get("itens") or []

    async def get_invoice(self, invoice_id: int) -> dict[str, Any] | None:
        return await self._get(f"/notas/{invoice_id}")

    async def get_product(self, product_id: int) -> dict[str, Any] | None:
        cached = self._product_cache.get(product_id)
        if cached and cached[0] > self._clock():
            return cached[1]
        product = await self._get(f"/produtos/{product_id}")
        if product is not None:
            expires_at = self._clock() + self._settings.product_cache_ttl_seconds
            self._product_cache[product_id] = (expires_at, product)
        return product

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any | None:
        """GET with auth. Returns None on 404."""
        url = f"{self._settings.olist_api_url}{path}"
        token = await self._auth.get_access_token()
        token_refreshed = False
        rate_limit_attempts = 0

        while True:
            response = await self._send(url, params, token)

            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                if rate_limit_attempts >= self._settings.olist_rate_limit_retries:
                    raise OlistRateLimited()
                wait = self._retry_wait(response, rate_limit_attempts)
                logger.warning("Olist rate limit on %s; retrying in %.1fs", path, wait)
                await self._sleep(wait)
                rate_limit_attempts += 1
                continue

            # 401 = expired token or user without permission on the module
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                if token_refreshed:
                    raise OlistForbidden()
                token = await self._auth.refresh_access_token(token)
                token_refreshed = True
                continue

            if response.status_code == HTTPStatus.NOT_FOUND:
                return None

            if not response.is_success:
                logger.warning(
                    "Olist GET %s returned %s: %s", path, response.status_code, response.text[:500]
                )
                raise OlistApiError()

            try:
                return response.json()
            except ValueError as exc:
                raise OlistApiError() from exc

    async def _send(self, url: str, params: dict[str, Any] | None, token: str) -> httpx.Response:
        try:
            return await self._http.get(
                url, params=params, headers={"Authorization": f"Bearer {token}"}
            )
        except httpx.HTTPError as exc:
            logger.warning("Olist request to %s failed: %r", url, exc)
            raise OlistApiError("Não foi possível conectar ao Olist.") from exc

    def _retry_wait(self, response: httpx.Response, attempt: int) -> float:
        backoff = self._settings.olist_rate_limit_backoff_seconds * 2**attempt
        try:
            wait = float(response.headers.get("Retry-After", backoff))
        except ValueError:
            wait = backoff
        return min(wait, MAX_RETRY_WAIT_SECONDS)
