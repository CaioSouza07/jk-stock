import pytest

from app.services.access_key import read_access_key
from app.services.invoice import InvoiceNotFound, InvoiceService
from tests.conftest import ACCESS_KEY
from tests.fakes import invoice_payload, item_payload, product_payload

pytestmark = pytest.mark.anyio

OTHER_KEY = "35240198765432000190550010000123451000000010"
KEY = read_access_key(ACCESS_KEY)


@pytest.fixture
def service(olist_client) -> InvoiceService:
    return InvoiceService(olist_client)


def add_invoices(fake_olist, *invoices):
    fake_olist.add("/notas", json={"itens": list(invoices), "paginacao": {"total": len(invoices)}})


async def test_lookup_picks_invoice_by_access_key(service, fake_olist):
    add_invoices(
        fake_olist,
        invoice_payload(OTHER_KEY, [item_payload(9)], invoice_id=2),
        invoice_payload(ACCESS_KEY, [item_payload(1, quantity=3)], invoice_id=1),
    )
    fake_olist.add(
        "/produtos/1", json=product_payload(1, ["https://img/1a.jpg", "https://img/1b.jpg"])
    )

    invoice = await service.lookup(KEY)

    assert invoice.id == 1
    assert invoice.access_key == ACCESS_KEY
    assert invoice.customer_name == "Cliente Teste"
    [item] = invoice.items
    assert item.product_id == 1
    assert item.quantity == 3
    assert item.total_price == 31.5
    assert item.image_url == "https://img/1a.jpg"
    assert item.images == ["https://img/1a.jpg", "https://img/1b.jpg"]
    assert fake_olist.api_requests("/produtos/9") == []


async def test_not_found(service, fake_olist):
    add_invoices(fake_olist, invoice_payload(OTHER_KEY, []))
    with pytest.raises(InvoiceNotFound):
        await service.lookup(KEY)


@pytest.mark.parametrize("list_items", [None, []])
async def test_fetches_detail_when_list_has_no_items(service, fake_olist, list_items):
    add_invoices(fake_olist, invoice_payload(ACCESS_KEY, list_items, invoice_id=7))
    fake_olist.add("/notas/7", json=invoice_payload(ACCESS_KEY, [item_payload(1)], invoice_id=7))
    fake_olist.add("/produtos/1", json=product_payload(1))

    invoice = await service.lookup(KEY)

    assert [i.product_id for i in invoice.items] == [1]
    assert len(fake_olist.api_requests("/notas/7")) == 1


@pytest.mark.parametrize("parent", [{"id": 50}, 50])
async def test_uses_parent_images_when_product_has_none(service, fake_olist, parent):
    add_invoices(fake_olist, invoice_payload(ACCESS_KEY, [item_payload(1)]))
    fake_olist.add("/produtos/1", json=product_payload(1, [], parent=parent))
    fake_olist.add("/produtos/50", json=product_payload(50, ["https://img/parent.jpg"]))

    invoice = await service.lookup(KEY)

    assert invoice.items[0].image_url == "https://img/parent.jpg"


async def test_product_errors_do_not_fail_lookup(service, fake_olist):
    add_invoices(fake_olist, invoice_payload(ACCESS_KEY, [item_payload(1), item_payload(2)]))
    fake_olist.add("/produtos/1", status=500)
    # /produtos/2 not registered -> 404

    invoice = await service.lookup(KEY)

    assert [i.images for i in invoice.items] == [[], []]


async def test_repeated_product_is_fetched_once(service, fake_olist):
    add_invoices(fake_olist, invoice_payload(ACCESS_KEY, [item_payload(1), item_payload(1)]))
    fake_olist.add("/produtos/1", json=product_payload(1, ["https://img/1.jpg"]))

    invoice = await service.lookup(KEY)

    assert [i.image_url for i in invoice.items] == ["https://img/1.jpg"] * 2
    assert len(fake_olist.api_requests("/produtos/1")) == 1
