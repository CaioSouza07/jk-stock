from datetime import UTC, datetime, timedelta

from app.services.token_store import OAuthTokens, TokenStore
from tests.fakes import token_payload

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


def test_save_and_load(tmp_path):
    store = TokenStore(tmp_path / "tokens.json")
    tokens = make_tokens()
    store.save(tokens)
    assert store.load() == tokens
    assert not (tmp_path / "tokens.json.tmp").exists()


def test_load_missing_file(tmp_path):
    assert TokenStore(tmp_path / "tokens.json").load() is None


def test_load_corrupted_file(tmp_path):
    path = tmp_path / "tokens.json"
    path.write_text("{not json", encoding="utf-8")
    assert TokenStore(path).load() is None
