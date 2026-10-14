from datetime import datetime

from pydantic import BaseModel, Field


class AuthStatusResponse(BaseModel):
    connected: bool = Field(description="True while the refresh token is still valid.")
    access_token_expires_at: datetime | None = None
    refresh_token_expires_at: datetime | None = None
