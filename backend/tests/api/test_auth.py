from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from tests.conftest import PASSWORD, build_app

FRONTEND = "https://app.example.com"


def login(client: TestClient, password: str | None = PASSWORD, **params: str):
    if password is not None:
        params["password"] = password
    return client.get("/auth/login", params=params, follow_redirects=False)


def login_state(client: TestClient, **params: str) -> str:
    r = login(client, **params)
    assert r.status_code == 302
    return parse_qs(urlsplit(r.headers["location"]).query)["state"][0]


def test_login_without_password(client):
    assert login(client, password=None).status_code == 401


def test_login_wrong_password(client):
    assert login(client, password="wrong").status_code == 401


def test_login_without_olist_credentials(settings, fake_olist):
    app = build_app(settings.model_copy(update={"olist_client_id": ""}), fake_olist)
    with TestClient(app) as client:
        r = login(client)
    assert r.status_code == 500
    assert "OLIST_CLIENT_ID" in r.json()["detail"]


def test_login_redirects_to_olist(client, settings):
    r = login(client)
    assert r.status_code == 302
    assert r.headers["location"].startswith(settings.olist_auth_url)
    state = parse_qs(urlsplit(r.headers["location"]).query)["state"][0]
    assert client.cookies.get("olist_oauth_state") == state


def test_callback_connects(client, settings, fake_olist):
    state = login_state(client)
    r = client.get("/auth/callback", params={"code": "the-code", "state": state})
    assert r.status_code == 200
    assert r.json() == {"detail": "Olist conectado com sucesso."}
    assert fake_olist.form()["code"] == "the-code"
    assert settings.tokens_file.exists()


def test_callback_wrong_state(client):
    login_state(client)
    r = client.get("/auth/callback", params={"code": "c", "state": "forged"})
    assert r.status_code == 400


def test_callback_without_login(client):
    r = client.get("/auth/callback", params={"code": "c", "state": "anything"})
    assert r.status_code == 400


def test_callback_login_denied(client, fake_olist):
    state = login_state(client)
    r = client.get("/auth/callback", params={"state": state, "error": "access_denied"})
    assert r.status_code == 502
    assert fake_olist.requests == []


def test_status_requires_password(client):
    assert client.get("/auth/status").status_code == 401


def test_status_not_connected(client, auth_headers):
    r = client.get("/auth/status", headers=auth_headers)
    assert r.json() == {
        "connected": False,
        "access_token_expires_at": None,
        "refresh_token_expires_at": None,
    }


def test_status_connected(client, auth_headers):
    state = login_state(client)
    client.get("/auth/callback", params={"code": "c", "state": state})
    body = client.get("/auth/status", headers=auth_headers).json()
    assert body["connected"] is True
    assert body["access_token_expires_at"] is not None


def test_login_cookie_not_secure_on_http(client):
    r = login(client)
    assert "secure" not in r.headers["set-cookie"].lower()


def test_login_cookie_secure_when_redirect_uri_is_https(settings, fake_olist):
    https = settings.model_copy(update={"olist_redirect_uri": "https://api.example.com/cb"})
    with TestClient(build_app(https, fake_olist)) as client:
        r = login(client)
    assert "secure" in r.headers["set-cookie"].lower()


def test_login_rejects_unknown_return_to(client):
    r = login(client, return_to="https://evil.example.com/")
    assert r.status_code == 400


def test_login_accepts_same_host_return_to(client):
    assert login(client, return_to="http://testserver/").status_code == 302


def test_callback_redirects_back_to_frontend(settings, fake_olist):
    app = build_app(settings.model_copy(update={"cors_origins": f"{FRONTEND}/;x"}), fake_olist)
    with TestClient(app) as client:
        state = login_state(client, return_to=f"{FRONTEND}/")
        r = client.get(
            "/auth/callback", params={"code": "c", "state": state}, follow_redirects=False
        )
    assert r.status_code == 302
    assert r.headers["location"] == f"{FRONTEND}/?olist=connected"
    assert settings.tokens_file.exists()


def test_callback_error_redirects_back_with_message(client, fake_olist):
    state = login_state(client, return_to="http://testserver/")
    r = client.get(
        "/auth/callback",
        params={"state": state, "error": "access_denied"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    location = urlsplit(r.headers["location"])
    assert "cancelado" in parse_qs(location.query)["olist_error"][0]
    assert fake_olist.requests == []


def test_status_when_token_storage_is_down(settings, fake_olist, auth_headers):
    # Upstash calls go through the fake transport, which does not know this host
    down = settings.model_copy(update={"upstash_redis_rest_url": "https://redis.invalid"})
    with TestClient(build_app(down, fake_olist)) as client:
        r = client.get("/auth/status", headers=auth_headers)
    assert r.status_code == 503
    assert "code" not in r.json()
