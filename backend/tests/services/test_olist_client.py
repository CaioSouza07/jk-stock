import httpx
import pytest

from app.services.olist_client import OlistApiError, OlistForbidden, OlistRateLimited
from tests.fakes import product_payload

pytestmark = pytest.mark.anyio


async def test_sends_bearer_token(olist_client, fake_olist):
    fake_olist.add("/produtos/1", json=product_payload(1))
    assert (await olist_client.get_product(1))["id"] == 1
    assert fake_olist.api_requests()[0].headers["Authorization"] == "Bearer access-0"


async def test_find_invoices_params(olist_client, fake_olist):
    fake_olist.add("/notas", json={"itens": [{"id": 1}], "paginacao": {}})
    assert await olist_client.find_invoices(12345) == [{"id": 1}]
    params = fake_olist.api_requests("/notas")[0].url.params
    assert params["numero"] == "12345"
    assert params["tipo"] == "S"


async def test_not_found_returns_none(olist_client):
    assert await olist_client.get_invoice(999) is None


async def test_rate_limit_retries_with_retry_after(olist_client, fake_olist, sleeps):
    fake_olist.add("/produtos/1", status=429, headers={"Retry-After": "7"})
    fake_olist.add("/produtos/1", json=product_payload(1))
    assert (await olist_client.get_product(1))["id"] == 1
    assert sleeps == [7.0]


async def test_rate_limit_exponential_backoff_then_gives_up(olist_client, fake_olist, sleeps):
    fake_olist.add("/produtos/1", status=429)
    with pytest.raises(OlistRateLimited):
        await olist_client.get_product(1)
    assert sleeps == [2.0, 4.0, 8.0]


async def test_401_refreshes_token_and_retries(olist_client, fake_olist):
    fake_olist.add("/produtos/1", status=401)
    fake_olist.add("/produtos/1", json=product_payload(1))
    assert (await olist_client.get_product(1))["id"] == 1
    assert fake_olist.issued == 1
    assert fake_olist.api_requests()[-1].headers["Authorization"] == "Bearer access-1"


async def test_401_after_refresh_is_forbidden(olist_client, fake_olist):
    fake_olist.add("/produtos/1", status=401)
    with pytest.raises(OlistForbidden):
        await olist_client.get_product(1)


async def test_server_error(olist_client, fake_olist):
    fake_olist.add("/produtos/1", status=500)
    with pytest.raises(OlistApiError):
        await olist_client.get_product(1)


async def test_connection_error(olist_client, fake_olist):
    fake_olist.error = httpx.ConnectError("boom")
    with pytest.raises(OlistApiError, match="Não foi possível conectar"):
        await olist_client.get_product(1)


async def test_product_cache(olist_client, fake_olist, monotonic, settings):
    fake_olist.add("/produtos/1", json=product_payload(1))
    await olist_client.get_product(1)
    await olist_client.get_product(1)
    assert len(fake_olist.api_requests()) == 1

    monotonic.now += settings.product_cache_ttl_seconds + 1
    await olist_client.get_product(1)
    assert len(fake_olist.api_requests()) == 2
