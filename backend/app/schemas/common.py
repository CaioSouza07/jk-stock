from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class MessageResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
