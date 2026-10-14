from tests.conftest import ACCESS_KEY
from tests.fakes import invoice_payload, item_payload, product_payload

URL = "/api/invoices/lookup"


def test_requires_password(client):
    assert client.post(URL, json={"barcode": ACCESS_KEY}).status_code == 401


def test_lookup(client, auth_headers, fake_olist, connected):
    fake_olist.add("/notas", json={"itens": [invoice_payload(ACCESS_KEY, [item_payload(1)])]})
    fake_olist.add("/produtos/1", json=product_payload(1, ["https://img/1.jpg"]))

    r = client.post(URL, json={"barcode": ACCESS_KEY}, headers=auth_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["access_key"] == ACCESS_KEY
    assert body["items"] == [
        {
            "product_id": 1,
            "code": "SKU-1",
            "description": "Produto 1",
            "unit": "UN",
            "quantity": 2.0,
            "unit_price": 10.5,
            "total_price": 21.0,
            "image_url": "https://img/1.jpg",
            "images": ["https://img/1.jpg"],
        }
    ]


def test_invalid_barcode(client, auth_headers, connected):
    r = client.post(URL, json={"barcode": "123"}, headers=auth_headers)
    assert r.status_code == 400


def test_not_connected(client, auth_headers):
    r = client.post(URL, json={"barcode": ACCESS_KEY}, headers=auth_headers)
    assert r.status_code == 503
    assert "não conectado" in r.json()["detail"]
    assert r.json()["code"] == "olist_not_connected"


def test_invoice_not_found(client, auth_headers, fake_olist, connected):
    fake_olist.add("/notas", json={"itens": []})
    r = client.post(URL, json={"barcode": ACCESS_KEY}, headers=auth_headers)
    assert r.status_code == 404
    assert r.json() == {"detail": "Nota fiscal não encontrada no Olist para esta chave de acesso."}
