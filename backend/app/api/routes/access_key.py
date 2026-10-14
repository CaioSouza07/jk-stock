from fastapi import APIRouter

from app.schemas.access_key import AccessKeyResponse, BarcodeRequest
from app.schemas.common import ErrorResponse
from app.services.access_key import AccessKey, read_access_key

router = APIRouter(prefix="/access-key", tags=["Access key"])


@router.post(
    "/validate",
    response_model=AccessKeyResponse,
    summary="Validate and parse the access key scanned by the camera",
    responses={400: {"model": ErrorResponse, "description": "Key not found or invalid"}},
)
def validate_access_key(body: BarcodeRequest) -> AccessKey:
    return read_access_key(body.barcode)
