"""Finds an invoice in Olist by access key and assembles its items with product images."""

import asyncio
import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from app.core.exceptions import AppError
from app.services.access_key import AccessKey
from app.services.olist_client import OlistApiError, OlistClient

logger = logging.getLogger(__name__)


class InvoiceNotFound(AppError):
    status_code = HTTPStatus.NOT_FOUND
    message = "Nota fiscal não encontrada no Olist para esta chave de acesso."


@dataclass(frozen=True)
class InvoiceItem:
    product_id: int | None
    code: str
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: float
    images: list[str]

    @property
    def image_url(self) -> str | None:
        return self.images[0] if self.images else None


@dataclass(frozen=True)
class Invoice:
    id: int
    number: str
    series: str
    access_key: str
    issued_at: str | None
    customer_name: str | None
    total: float
    items: list[InvoiceItem]


class InvoiceService:
    def __init__(self, client: OlistClient, max_concurrency: int = 3) -> None:
        self._client = client
        # Keeps product lookups under the Olist rate limit (30 req/min)
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def lookup(self, key: AccessKey) -> Invoice:
        invoices = await self._client.find_invoices(key.invoice_number)
        invoice = next((i for i in invoices if i.get("chaveAcesso") == key.key), None)
        if invoice is None:
            raise InvoiceNotFound()

        raw_items = invoice.get("itens")
        if raw_items is None:
            detail = await self._client.get_invoice(invoice["id"]) or {}
            raw_items = detail.get("itens") or []

        product_ids = list({item["idProduto"] for item in raw_items if item.get("idProduto")})
        images = await asyncio.gather(*(self._product_images(pid) for pid in product_ids))
        images_by_product = dict(zip(product_ids, images, strict=True))

        return Invoice(
            id=invoice["id"],
            number=invoice.get("numero") or "",
            series=invoice.get("serie") or "",
            access_key=key.key,
            issued_at=invoice.get("dataEmissao"),
            customer_name=(invoice.get("cliente") or {}).get("nome"),
            total=float(invoice.get("valor") or 0),
            items=[_to_item(item, images_by_product) for item in raw_items],
        )

    async def _product_images(self, product_id: int) -> list[str]:
        """Best-effort: an Olist failure here must not fail the whole lookup."""
        async with self._semaphore:
            try:
                product = await self._client.get_product(product_id)
                urls = _image_urls(product)
                parent_id = _parent_id(product)
                if not urls and parent_id:
                    urls = _image_urls(await self._client.get_product(parent_id))
                return urls
            except OlistApiError as exc:
                logger.warning("Could not load images for product %s: %s", product_id, exc.message)
                return []


def _image_urls(product: dict[str, Any] | None) -> list[str]:
    return [a["url"] for a in (product or {}).get("anexos") or [] if a.get("url")]


def _parent_id(product: dict[str, Any] | None) -> int | None:
    parent = (product or {}).get("produtoPai")
    if isinstance(parent, dict):
        return parent.get("id")
    return parent if isinstance(parent, int) else None


def _to_item(raw: dict[str, Any], images_by_product: dict[int, list[str]]) -> InvoiceItem:
    product_id = raw.get("idProduto") or None
    return InvoiceItem(
        product_id=product_id,
        code=raw.get("codigo") or "",
        description=raw.get("descricao") or "",
        unit=raw.get("unidade") or "",
        quantity=float(raw.get("quantidade") or 0),
        unit_price=float(raw.get("valorUnitario") or 0),
        total_price=float(raw.get("valorTotal") or 0),
        images=images_by_product.get(product_id, []),
    )
