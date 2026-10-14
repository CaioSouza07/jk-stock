import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.services.token_store import (
    FileTokenStore,
    OAuthTokens,
    TokenStoreError,
    UpstashTokenStore,
    create_token_store,
)
from tests.fakes import token_payload

UPSTASH_URL = "https://fake.upstash.io"
UPSTASH_KEY = "jkstock:olist_tokens"

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def make_tokens() -> OAuthTokens:
    return OAuthTokens.from_token_response(token_payload(1), NOW)


def test_from_token_response_sets_expirations():
    tokens = make_tokens()
    assert tokens.access_token == "access-1"
    assert tokens.access_expires_at == NOW + timedelta(hours=4)
    assert tokens.refresh_expires_at == NOW + timedelta(days=1)


def test_zero_refresh_ttl_falls_back_to_default():
    data = {**token_payload(1), "refresh_expires_in": 0}
    tokens = OAuthTokens.from_token_response(data, NOW)
    assert tokens.refresh_expires_at == NOW + timedelta(days=1)


def test_access_expired_uses_safety_margin():
    tokens = make_tokens()
    assert not tokens.access_expired(NOW + timedelta(hours=3, minutes=54))
    assert tokens.access_expired(NOW + timedelta(hours=3, minutes=56))


@pytest.mark.anyio
async def test_save_and_load(tmp_path):
    store = FileTokenStore(tmp_path / "tokens.json")
    tokens = make_tokens()
    await store.save(tokens)
    assert await store.load() == tokens
    assert not (tmp_path / "tokens.json.tmp").exists()


@pytest.mark.anyio
async def test_load_missing_file(tmp_path):
    assert await FileTokenStore(tmp_path / "tokens.json").load() is None


@pytest.mark.anyio
async def test_load_corrupted_file(tmp_path):
    path = tmp_path / "tokens.json"
    path.write_text("{not json", encoding="utf-8")
    assert await FileTokenStore(path).load() is None


class FakeUpstash:
    """Minimal Upstash REST API: GET/SET on an in-memory dict."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.auth_headers: list[str] = []
        self.status = 200

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.auth_headers.append(request.headers["authorization"])
        if self.status != 200:
            return httpx.Response(self.status, json={"error": "boom"})
        command, key, *rest = json.loads(request.content)
        if command == "SET":
            self.data[key] = rest[0]
            return httpx.Response(200, json={"result": "OK"})
        return httpx.Response(200, json={"result": self.data.get(key)})


@pytest.fixture
def upstash() -> FakeUpstash:
    return FakeUpstash()


@pytest.fixture
async def upstash_store(upstash):
    async with httpx.AsyncClient(transport=httpx.MockTransport(upstash.handler)) as http:
        yield UpstashTokenStore(http, UPSTASH_URL + "/", "secret", UPSTASH_KEY)


@pytest.mark.anyio
async def test_upstash_save_and_load(upstash_store, upstash):
    tokens = make_tokens()
    await upstash_store.save(tokens)
    assert json.loads(upstash.data[UPSTASH_KEY]) == tokens.to_dict()
    assert await upstash_store.load() == tokens
    assert set(upstash.auth_headers) == {"Bearer secret"}


@pytest.mark.anyio
async def test_upstash_load_missing_key(upstash_store):
    assert await upstash_store.load() is None


@pytest.mark.anyio
async def test_upstash_load_corrupted_value(upstash_store, upstash):
    upstash.data[UPSTASH_KEY] = "{not json"
    assert await upstash_store.load() is None


@pytest.mark.anyio
async def test_upstash_error_is_not_treated_as_disconnected(upstash_store, upstash):
    upstash.status = 401
    with pytest.raises(TokenStoreError):
        await upstash_store.load()
    with pytest.raises(TokenStoreError):
        await upstash_store.save(make_tokens())


@pytest.mark.anyio
async def test_upstash_connection_error():
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    async with httpx.AsyncClient(transport=httpx.MockTransport(fail)) as http:
        store = UpstashTokenStore(http, UPSTASH_URL, "secret", UPSTASH_KEY)
        with pytest.raises(TokenStoreError):
            await store.load()


@pytest.mark.anyio
async def test_create_token_store(settings):
    async with httpx.AsyncClient() as http:
        assert isinstance(create_token_store(settings, http), FileTokenStore)
        upstash_settings = settings.model_copy(update={"upstash_redis_rest_url": UPSTASH_URL})
        assert isinstance(create_token_store(upstash_settings, http), UpstashTokenStore)
