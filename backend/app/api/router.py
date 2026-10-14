"""Aggregates the routes under /api (all require the X-App-Password header)."""

from fastapi import APIRouter, Depends

from app.api.routes import access_key, invoice
from app.core.security import verify_app_password
from app.schemas.common import ErrorResponse

api_router = APIRouter(
    prefix="/api",
    dependencies=[Depends(verify_app_password)],
    responses={401: {"model": ErrorResponse, "description": "Invalid or missing app password"}},
)
api_router.include_router(access_key.router)
api_router.include_router(invoice.router)
