from fastapi import APIRouter

from app.api.deps import InvoiceServiceDep
from app.schemas.access_key import BarcodeRequest
from app.schemas.common import ErrorResponse
from app.schemas.invoice import InvoiceResponse
from app.services.access_key import read_access_key
from app.services.invoice import Invoice

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post(
    "/lookup",
    response_model=InvoiceResponse,
    summary="Find the scanned invoice in Olist, with its items and product images",
    responses={
        400: {"model": ErrorResponse, "description": "Access key not found or invalid"},
        404: {"model": ErrorResponse, "description": "Invoice not found in Olist"},
        502: {"model": ErrorResponse, "description": "Olist error or access denied"},
        503: {"model": ErrorResponse, "description": "Olist not connected or rate limited"},
    },
)
async def lookup_invoice(body: BarcodeRequest, invoice_service: InvoiceServiceDep) -> Invoice:
    return await invoice_service.lookup(read_access_key(body.barcode))
