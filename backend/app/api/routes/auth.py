import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.deps import OlistAuthDep
from app.core.config import SettingsDep
from app.core.security import check_app_password, verify_app_password
from app.schemas.auth import AuthStatusResponse
from app.schemas.common import ErrorResponse, MessageResponse
from app.services.olist_auth import InvalidOAuthState, OlistAuthError

STATE_COOKIE = "olist_oauth_state"
STATE_MAX_AGE_SECONDS = 600

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/login",
    summary="Start the Olist login (open in the browser)",
    status_code=302,
    responses={
        302: {"description": "Redirect to the Olist login page"},
        401: {"model": ErrorResponse, "description": "Invalid or missing app password"},
        500: {"model": ErrorResponse, "description": "Olist credentials not configured"},
    },
)
def login(
    olist_auth: OlistAuthDep,
    settings: SettingsDep,
    password: Annotated[str | None, Query(description="App password (APP_PASSWORD).")] = None,
) -> RedirectResponse:
    check_app_password(password, settings)
    olist_auth.ensure_configured()

    state = secrets.token_urlsafe(32)
    response = RedirectResponse(olist_auth.authorization_url(state), status_code=302)
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=STATE_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/auth",
    )
    return response


@router.get(
    "/callback",
    response_model=MessageResponse,
    summary="OAuth callback called by Olist after login",
    responses={
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
) -> JSONResponse:
    expected_state = request.cookies.get(STATE_COOKIE)
    if not (state and expected_state and secrets.compare_digest(state, expected_state)):
        raise InvalidOAuthState()
    if error or not code:
        raise OlistAuthError("Login no Olist cancelado ou não autorizado.")

    await olist_auth.exchange_code(code)

    response = JSONResponse({"detail": "Olist conectado com sucesso."})
    response.delete_cookie(STATE_COOKIE, path="/auth")
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
