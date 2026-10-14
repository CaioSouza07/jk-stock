import secrets
from typing import Annotated
from urllib.parse import urlencode, urlsplit

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.api.deps import OlistAuthDep
from app.core.config import Settings, SettingsDep
from app.core.exceptions import AppError
from app.core.security import check_app_password, verify_app_password
from app.schemas.auth import AuthStatusResponse
from app.schemas.common import ErrorResponse, MessageResponse
from app.services.olist_auth import InvalidOAuthState, OlistAuthError

STATE_COOKIE = "olist_oauth_state"
RETURN_TO_COOKIE = "olist_oauth_return_to"
STATE_MAX_AGE_SECONDS = 600

router = APIRouter(prefix="/auth", tags=["Auth"])


class InvalidReturnTo(AppError):
    message = "Endereço de retorno não permitido."


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}".lower()


def _validate_return_to(return_to: str, request: Request, settings: Settings) -> None:
    """Only redirect back to an allowed frontend (CORS_ORIGINS) or to this same host."""
    parts = urlsplit(return_to)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise InvalidReturnTo()
    allowed = {o.lower() for o in settings.cors_origin_list}
    same_host = parts.netloc.lower() == request.headers.get("host", "").lower()
    if _origin(return_to) not in allowed and not same_host:
        raise InvalidReturnTo()


def _with_query(url: str, params: dict[str, str]) -> str:
    separator = "&" if urlsplit(url).query else "?"
    return f"{url}{separator}{urlencode(params)}"


def _clear_login_cookies(response: Response) -> None:
    response.delete_cookie(STATE_COOKIE, path="/auth")
    response.delete_cookie(RETURN_TO_COOKIE, path="/auth")


@router.get(
    "/login",
    summary="Start the Olist login (open in the browser)",
    status_code=302,
    responses={
        302: {"description": "Redirect to the Olist login page"},
        400: {"model": ErrorResponse, "description": "return_to not allowed"},
        401: {"model": ErrorResponse, "description": "Invalid or missing app password"},
        500: {"model": ErrorResponse, "description": "Olist credentials not configured"},
    },
)
def login(
    request: Request,
    olist_auth: OlistAuthDep,
    settings: SettingsDep,
    password: Annotated[str | None, Query(description="App password (APP_PASSWORD).")] = None,
    return_to: Annotated[
        str | None, Query(description="Frontend URL to go back to after the login.")
    ] = None,
) -> RedirectResponse:
    check_app_password(password, settings)
    olist_auth.ensure_configured()
    if return_to:
        _validate_return_to(return_to, request, settings)

    state = secrets.token_urlsafe(32)
    response = RedirectResponse(olist_auth.authorization_url(state), status_code=302)
    cookies = {STATE_COOKIE: state, RETURN_TO_COOKIE: return_to}
    for name, value in cookies.items():
        if not value:
            continue
        response.set_cookie(
            name,
            value,
            max_age=STATE_MAX_AGE_SECONDS,
            httponly=True,
            secure=settings.use_secure_cookies,
            samesite="lax",
            path="/auth",
        )
    return response


@router.get(
    "/callback",
    response_model=MessageResponse,
    summary="OAuth callback called by Olist after login",
    responses={
        302: {"description": "Back to the frontend (when the login started with return_to)"},
        400: {"model": ErrorResponse, "description": "Invalid or expired login state"},
        502: {"model": ErrorResponse, "description": "Olist denied or failed the login"},
    },
)
async def callback(
    request: Request,
    olist_auth: OlistAuthDep,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> Response:
    return_to = request.cookies.get(RETURN_TO_COOKIE)
    try:
        expected_state = request.cookies.get(STATE_COOKIE)
        if not (state and expected_state and secrets.compare_digest(state, expected_state)):
            raise InvalidOAuthState()
        if error or not code:
            raise OlistAuthError("Login no Olist cancelado ou não autorizado.")
        await olist_auth.exchange_code(code)
    except AppError as exc:
        if not return_to:
            raise
        response = RedirectResponse(_with_query(return_to, {"olist_error": exc.message}), 302)
    else:
        if return_to:
            response = RedirectResponse(_with_query(return_to, {"olist": "connected"}), 302)
        else:
            response = JSONResponse({"detail": "Olist conectado com sucesso."})

    _clear_login_cookies(response)
    return response


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="Olist connection status",
    dependencies=[Depends(verify_app_password)],
    responses={401: {"model": ErrorResponse, "description": "Invalid or missing app password"}},
)
def auth_status(olist_auth: OlistAuthDep) -> AuthStatusResponse:
    tokens = olist_auth.current_tokens()
    if tokens is None:
        return AuthStatusResponse(connected=False)
    return AuthStatusResponse(
        connected=olist_auth.is_connected(tokens),
        access_token_expires_at=tokens.access_expires_at,
        refresh_token_expires_at=tokens.refresh_expires_at,
    )
