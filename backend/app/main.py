import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.api.router import api_router
from app.api.routes import auth, health
from app.core.config import Settings, get_settings
from app.core.handlers import register_exception_handlers
from app.services.invoice import InvoiceService
from app.services.olist_auth import OlistAuth
from app.services.olist_client import OlistClient
from app.services.token_store import TokenStore


def _start_token_refresh(olist_auth: OlistAuth, settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        olist_auth.refresh_if_connected,
        "interval",
        minutes=settings.token_refresh_interval_minutes,
        id="olist_token_refresh",
        # Also run on startup: the refresh token may be close to expiring after downtime
        next_run_time=datetime.now(UTC),
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    return scheduler


def create_app(
    settings: Settings | None = None,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """http_transport lets tests replace Olist with an httpx.MockTransport."""
    settings = settings or get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, transport=http_transport
        ) as http:
            olist_auth = OlistAuth(settings, http, TokenStore(settings.tokens_file))
            app.state.olist_auth = olist_auth
            app.state.invoice_service = InvoiceService(
                OlistClient(settings, http, olist_auth), settings.olist_max_concurrency
            )
            scheduler = None
            if settings.token_refresh_enabled:
                scheduler = _start_token_refresh(olist_auth, settings)
            try:
                yield
            finally:
                if scheduler:
                    scheduler.shutdown(wait=False)

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(api_router)
    return app


app = create_app()
