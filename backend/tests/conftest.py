from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app
from app.services.token_store import OAuthTokens, TokenStore
from tests.fakes import FakeOlist, token_payload

PASSWORD = "test-password"
ACCESS_KEY = "35240112345678000190550010000123451000000013"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def settings(tmp_path) -> Settings:
    # _env_file=None: tests never read the real .env
    return Settings(
        _env_file=None,
        app_password=PASSWORD,
        olist_client_id="client-id",
        olist_client_secret="client-secret",
        tokens_file=tmp_path / "tokens.json",
        token_refresh_enabled=False,
    )


@pytest.fixture
def fake_olist() -> FakeOlist:
    return FakeOlist()


def build_app(settings: Settings, fake_olist: FakeOlist) -> FastAPI:
    app = create_app(settings, http_transport=fake_olist.transport)
    app.dependency_overrides[get_settings] = lambda: settings
    return app


@pytest.fixture
def app(settings: Settings, fake_olist: FakeOlist) -> FastAPI:
    return build_app(settings, fake_olist)


@pytest.fixture
def client(app: FastAPI):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-App-Password": PASSWORD}


@pytest.fixture
def connected(settings: Settings) -> OAuthTokens:
    """Olist already connected: valid tokens "access-0" / "refresh-0" on disk."""
    tokens = OAuthTokens.from_token_response(token_payload(0), datetime.now(UTC))
    TokenStore(settings.tokens_file).save(tokens)
    return tokens
