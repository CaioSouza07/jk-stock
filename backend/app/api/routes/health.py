from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Check if the API is up")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
