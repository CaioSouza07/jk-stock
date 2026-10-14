from app.core.config import Settings, get_settings
from tests.conftest import ACCESS_KEY

URL = "/api/access-key/validate"


def test_validate_access_key(client, auth_headers):
    r = client.post(URL, json={"barcode": ACCESS_KEY}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["key"] == ACCESS_KEY
    assert body["invoice_number"] == 12345
    assert body["cnpj"] == "12345678000190"


def test_missing_password(client):
    r = client.post(URL, json={"barcode": ACCESS_KEY})
    assert r.status_code == 401
    assert r.json() == {"detail": "Senha do app inválida ou ausente."}


def test_wrong_password(client):
    r = client.post(URL, json={"barcode": ACCESS_KEY}, headers={"X-App-Password": "wrong"})
    assert r.status_code == 401


def test_password_not_configured(app, client, auth_headers):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, app_password="")
    r = client.post(URL, json={"barcode": ACCESS_KEY}, headers=auth_headers)
    assert r.status_code == 500
    assert r.json() == {"detail": "APP_PASSWORD não configurada no servidor."}


def test_invalid_key(client, auth_headers):
    r = client.post(URL, json={"barcode": ACCESS_KEY[:43] + "4"}, headers=auth_headers)
    assert r.status_code == 400
    assert "dígito verificador" in r.json()["detail"]


def test_invalid_body(client, auth_headers):
    r = client.post(URL, json={"barcode": ""}, headers=auth_headers)
    assert r.status_code == 422
    assert r.json()["detail"] == "Dados inválidos na requisição."
    assert r.json()["errors"][0]["field"] == "body.barcode"
