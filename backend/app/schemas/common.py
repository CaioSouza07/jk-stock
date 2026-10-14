from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class MessageResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
