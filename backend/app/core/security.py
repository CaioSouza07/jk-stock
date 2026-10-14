import secrets
from typing import Annotated

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.core.config import Settings, SettingsDep
from app.core.exceptions import MissingConfiguration, Unauthorized

app_password_header = APIKeyHeader(
    name="X-App-Password",
    auto_error=False,
    description="App password (APP_PASSWORD in .env).",
)


def check_app_password(password: str | None, settings: Settings) -> None:
    expected = settings.app_password.get_secret_value()
    if not expected:
        raise MissingConfiguration("APP_PASSWORD não configurada no servidor.")
    if not password or not secrets.compare_digest(password.encode(), expected.encode()):
        raise Unauthorized()


def verify_app_password(
    password: Annotated[str | None, Security(app_password_header)],
    settings: SettingsDep,
) -> None:
    check_app_password(password, settings)
