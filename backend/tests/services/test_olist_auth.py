import asyncio
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import MissingConfiguration
from app.services.olist_auth import OlistAuth, OlistAuthError, OlistNotConnected
from app.services.token_store import FileTokenStore

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = NOW

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(settings) -> FileTokenStore:
    return FileTokenStore(settings.tokens_file)


@pytest.fixture
async def olist_auth(settings, store, fake_olist, clock):
    async with httpx.AsyncClient(transport=fake_olist.transport) as http:
        yield OlistAuth(settings, http, store, now=clock)


async def test_authorization_url(olist_auth, settings):
    url = urlsplit(olist_auth.authorization_url("abc"))
    assert f"{url.scheme}://{url.netloc}{url.path}" == settings.olist_auth_url
    assert {k: v[0] for k, v in parse_qs(url.query).items()} == {
        "client_id": "client-id",
        "redirect_uri": settings.olist_redirect_uri,
        "scope": "openid",
        "response_type": "code",
        "state": "abc",
    }


async def test_missing_credentials(store, fake_olist):
    async with httpx.AsyncClient(transport=fake_olist.transport) as http:
        auth = OlistAuth(Settings(_env_file=None), http, store)
        with pytest.raises(MissingConfiguration):
            await auth.exchange_code("code")
    assert fake_olist.requests == []


async def test_exchange_code_saves_tokens(olist_auth, store, fake_olist, settings):
    tokens = await olist_auth.exchange_code("the-code")
    assert tokens.access_token == "access-1"
    assert (await store.load()) == tokens
    assert fake_olist.form() == {
        "grant_type": "authorization_code",
        "code": "the-code",
        "redirect_uri": settings.olist_redirect_uri,
        "client_id": "client-id",
        "client_secret": "client-secret",
    }


async def test_exchange_code_rejected(olist_auth, store, fake_olist):
    fake_olist.token_status = 400
    with pytest.raises(OlistAuthError):
        await olist_auth.exchange_code("bad-code")
    assert (await store.load()) is None


async def test_connection_error(olist_auth, fake_olist):
    fake_olist.error = httpx.ConnectError("boom")
    with pytest.raises(OlistAuthError, match="Não foi possível conectar"):
        await olist_auth.exchange_code("code")


async def test_get_access_token_not_connected(olist_auth):
    with pytest.raises(OlistNotConnected):
        await olist_auth.get_access_token()


async def test_get_access_token_still_valid(olist_auth, fake_olist, clock):
    await olist_auth.exchange_code("code")
    clock.now += timedelta(hours=1)
    assert await olist_auth.get_access_token() == "access-1"
    assert len(fake_olist.requests) == 1


async def test_get_access_token_refreshes_when_expired(olist_auth, store, fake_olist, clock):
    await olist_auth.exchange_code("code")
    clock.now += timedelta(hours=4)
    assert await olist_auth.get_access_token() == "access-2"
    assert fake_olist.form()["grant_type"] == "refresh_token"
    assert fake_olist.form()["refresh_token"] == "refresh-1"
    assert (await store.load()).refresh_token == "refresh-2"


async def test_concurrent_requests_refresh_once(olist_auth, fake_olist, clock):
    await olist_auth.exchange_code("code")
    clock.now += timedelta(hours=4)
    results = await asyncio.gather(*(olist_auth.get_access_token() for _ in range(5)))
    assert results == ["access-2"] * 5
    assert fake_olist.issued == 2


async def test_refresh_token_expired(olist_auth, fake_olist, clock):
    await olist_auth.exchange_code("code")
    clock.now += timedelta(hours=25)
    with pytest.raises(OlistNotConnected, match="expirada"):
        await olist_auth.get_access_token()
    assert len(fake_olist.requests) == 1


async def test_refresh_rejected_by_olist(olist_auth, fake_olist, clock):
    await olist_auth.exchange_code("code")
    clock.now += timedelta(hours=4)
    fake_olist.token_status = 400
    with pytest.raises(OlistNotConnected, match="expirada"):
        await olist_auth.get_access_token()


async def test_scheduled_refresh_without_tokens(olist_auth, fake_olist):
    await olist_auth.refresh_if_connected()
    assert fake_olist.requests == []


async def test_scheduled_refresh(olist_auth, store):
    await olist_auth.exchange_code("code")
    await olist_auth.refresh_if_connected()
    assert (await store.load()).access_token == "access-2"


async def test_scheduled_refresh_swallows_errors(olist_auth, store, fake_olist):
    await olist_auth.exchange_code("code")
    fake_olist.token_status = 500
    await olist_auth.refresh_if_connected()
    assert (await store.load()).access_token == "access-1"
