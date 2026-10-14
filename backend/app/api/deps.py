from typing import Annotated

from fastapi import Depends, Request

from app.services.invoice import InvoiceService
from app.services.olist_auth import OlistAuth


def get_olist_auth(request: Request) -> OlistAuth:
    return request.app.state.olist_auth


def get_invoice_service(request: Request) -> InvoiceService:
    return request.app.state.invoice_service


OlistAuthDep = Annotated[OlistAuth, Depends(get_olist_auth)]
InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]
