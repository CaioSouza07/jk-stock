from fastapi.testclient import TestClient

from tests.conftest import build_app

ORIGIN = "https://app.example.com"


def cors_client(settings, fake_olist, cors_origins: str) -> TestClient:
    app = build_app(settings.model_copy(update={"cors_origins": cors_origins}), fake_olist)
    return TestClient(app)


def preflight(client: TestClient, origin: str):
    return client.options(
        "/api/invoices/lookup",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-app-password",
        },
    )


def test_cors_allows_configured_origins(settings, fake_olist):
    with cors_client(settings, fake_olist, f" {ORIGIN}/ ; https://other.example.com;") as c:
        for origin in (ORIGIN, "https://other.example.com"):
            r = preflight(c, origin)
            assert r.status_code == 200
            assert r.headers["access-control-allow-origin"] == origin


def test_cors_rejects_other_origins(settings, fake_olist):
    with cors_client(settings, fake_olist, ORIGIN) as c:
        r = preflight(c, "https://evil.example.com")
    assert "access-control-allow-origin" not in r.headers
