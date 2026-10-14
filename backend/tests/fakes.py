from typing import Any
from urllib.parse import parse_qs

import httpx

API_PREFIX = "/public-api/v3"


def token_payload(n: int) -> dict[str, Any]:
    return {
        "access_token": f"access-{n}",
        "refresh_token": f"refresh-{n}",
        "expires_in": 4 * 3600,
        "refresh_expires_in": 24 * 3600,
        "token_type": "Bearer",
    }


def item_payload(product_id: int, code: str = "SKU-1", quantity: int = 2) -> dict[str, Any]:
    return {
        "idItem": product_id * 10,
        "idProduto": product_id,
        "codigo": code,
        "descricao": f"Produto {product_id}",
        "unidade": "UN",
        "quantidade": quantity,
        "valorUnitario": 10.5,
        "valorTotal": 10.5 * quantity,
    }


def invoice_payload(
    access_key: str, items: list[dict[str, Any]] | None, invoice_id: int = 1
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": invoice_id,
        "numero": "12345",
        "serie": "1",
        "chaveAcesso": access_key,
        "dataEmissao": "2024-01-15",
        "cliente": {"nome": "Cliente Teste"},
        "valor": 42.0,
    }
    if items is not None:
        payload["itens"] = items
    return payload


def product_payload(product_id: int, urls: list[str] = (), parent: Any = None) -> dict[str, Any]:
    return {
        "id": product_id,
        "produtoPai": parent,
        "anexos": [{"id": i, "url": url, "externo": False} for i, url in enumerate(urls)],
    }


class FakeOlist:
    """Stands in for Olist (token endpoint + API v3) through httpx.MockTransport.

    API responses are queued per path with add(); the last one is repeated.
    """

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.token_status = 200
        self.error: Exception | None = None
        self.issued = 0
        self._api: dict[str, list[tuple[int, Any, dict[str, str]]]] = {}
        self.transport = httpx.MockTransport(self._handle)

    def add(
        self, path: str, json: Any = None, status: int = 200, headers: dict[str, str] | None = None
    ) -> None:
        self._api.setdefault(path, []).append((status, json, headers or {}))

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.error:
            raise self.error
        if request.url.path.endswith("/openid-connect/token"):
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "invalid_grant"})
            self.issued += 1
            return httpx.Response(200, json=token_payload(self.issued))

        queue = self._api.get(request.url.path.removeprefix(API_PREFIX))
        if not queue:
            return httpx.Response(404, json={"mensagem": "not found"})
        status, json, headers = queue.pop(0) if len(queue) > 1 else queue[0]
        return httpx.Response(status, json=json, headers=headers)

    def form(self, index: int = -1) -> dict[str, str]:
        body = self.requests[index].content.decode()
        return {k: v[0] for k, v in parse_qs(body).items()}

    def api_requests(self, path: str | None = None) -> list[httpx.Request]:
        return [
            r
            for r in self.requests
            if r.url.path.startswith(API_PREFIX)
            and (path is None or r.url.path == API_PREFIX + path)
        ]
