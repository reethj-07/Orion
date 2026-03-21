"""Authentication routes: register, login, refresh, and logout."""

from fastapi import APIRouter, Body, Cookie, Request, Response

from app.api.responses import success_envelope
from app.core.config import Settings
from app.core.dependencies import AuthServiceDep, SettingsDep
from app.core.exceptions import UnauthorizedError
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.common import APIResponse

router = APIRouter()


def _set_auth_cookies(response: Response, tokens: TokenPair, settings: Settings) -> None:
    """
    Attach HTTP-only cookies for access and refresh tokens.

    Args:
        response: Outgoing HTTP response.
        tokens: Issued token pair.
        settings: Application settings controlling cookie security flags.
    """
    access_max_age = settings.jwt_access_token_expire_minutes * 60
    refresh_max_age = settings.jwt_refresh_token_expire_days * 86400
    response.set_cookie(
        key="orion_access",
        value=tokens.access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=access_max_age,
        path="/",
    )
    response.set_cookie(
        key="orion_refresh",
        value=tokens.refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=refresh_max_age,
        path="/",
    )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    """
    Remove authentication cookies from the client.

    Args:
        response: Outgoing HTTP response.
        settings: Application settings controlling cookie security flags.
    """
    response.delete_cookie(
        key="orion_access",
        path="/",
        secure=settings.cookie_secure,
        samesite="lax",
    )
    response.delete_cookie(
        key="orion_refresh",
        path="/",
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post("/register", response_model=APIResponse[AuthResponse])
async def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    service: AuthServiceDep,
    settings: SettingsDep,
) -> APIResponse[AuthResponse]:
    """
    Register a new organization and its initial administrator account.

    Args:
        request: Incoming HTTP request.
        response: Outgoing HTTP response used to set cookies.
        payload: Registration body.
        service: Authentication service.
        settings: Application settings.

    Returns:
        API envelope with tokens and user projection.
    """
    result = await service.register(payload)
    _set_auth_cookies(response, result.tokens, settings)
    return success_envelope(request, result)


@router.post("/login", response_model=APIResponse[AuthResponse])
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    service: AuthServiceDep,
    settings: SettingsDep,
) -> APIResponse[AuthResponse]:
    """
    Authenticate with email and password credentials.

    Args:
        request: Incoming HTTP request.
        response: Outgoing HTTP response used to set cookies.
        payload: Login body.
        service: Authentication service.
        settings: Application settings.

    Returns:
        API envelope with tokens and user projection.
    """
    result = await service.login(payload)
    _set_auth_cookies(response, result.tokens, settings)
    return success_envelope(request, result)


@router.post("/refresh", response_model=APIResponse[TokenPair])
async def refresh(
    request: Request,
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    body: RefreshRequest | None = Body(default=None),
    refresh_cookie: str | None = Cookie(default=None, alias="orion_refresh"),
) -> APIResponse[TokenPair]:
    """
    Obtain a new token pair using a refresh token from the body or cookie.

    Args:
        request: Incoming HTTP request.
        response: Outgoing HTTP response used to refresh cookies.
        service: Authentication service.
        settings: Application settings.
        body: Optional JSON body carrying a refresh token.
        refresh_cookie: Optional HTTP-only refresh cookie.

    Returns:
        API envelope with a rotated token pair.
    """
    refresh_token = (body.refresh_token if body and body.refresh_token else None) or refresh_cookie
    if refresh_token is None:
        raise UnauthorizedError("Missing refresh token")
    tokens = await service.refresh(refresh_token)
    _set_auth_cookies(response, tokens, settings)
    return success_envelope(request, tokens)


@router.post("/logout", response_model=APIResponse[MessageResponse])
async def logout(
    request: Request,
    response: Response,
    service: AuthServiceDep,
    settings: SettingsDep,
    body: RefreshRequest | None = Body(default=None),
    refresh_cookie: str | None = Cookie(default=None, alias="orion_refresh"),
) -> APIResponse[MessageResponse]:
    """
    Revoke the active refresh token and clear authentication cookies.

    Args:
        request: Incoming HTTP request.
        response: Outgoing HTTP response used to clear cookies.
        service: Authentication service.
        settings: Application settings.
        body: Optional JSON body carrying a refresh token.
        refresh_cookie: Optional HTTP-only refresh cookie.

    Returns:
        API envelope confirming logout.
    """
    refresh_token = (body.refresh_token if body and body.refresh_token else None) or refresh_cookie
    await service.logout(refresh_token)
    _clear_auth_cookies(response, settings)
    return success_envelope(request, MessageResponse(message="Logged out"))
