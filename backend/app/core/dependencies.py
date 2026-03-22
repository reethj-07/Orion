"""FastAPI dependency callables for configuration and infrastructure handles."""

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Cookie, Depends, Header, Request
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.infra_types import MotorDatabase, RedisJSON
from app.core.principal import AuthPrincipal
from app.models.user import UserRole
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService


async def get_settings_dep() -> Settings:
    """Return application settings (cached)."""
    return get_settings()


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """
    Yield an async SQLAlchemy session scoped to the request.

    Args:
        request: Starlette request carrying application state.

    Yields:
        AsyncSession bound to the configured engine.
    """
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_mongo_db(request: Request) -> MotorDatabase:
    """
    Return the Motor database handle from application state.

    Args:
        request: Starlette request carrying application state.

    Returns:
        AsyncIOMotorDatabase for the configured database name.
    """
    return cast(MotorDatabase, request.app.state.mongo_db)


def get_redis(request: Request) -> RedisJSON:
    """
    Return the shared asyncio Redis client.

    Args:
        request: Starlette request carrying application state.

    Returns:
        Redis client instance.
    """
    return cast(RedisJSON, request.app.state.redis)


def get_qdrant(request: Request) -> AsyncQdrantClient:
    """
    Return the async Qdrant client from application state.

    Args:
        request: Starlette request carrying application state.

    Returns:
        AsyncQdrantClient instance.
    """
    return cast(AsyncQdrantClient, request.app.state.qdrant)


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
MongoDb = Annotated[MotorDatabase, Depends(get_mongo_db)]
RedisDep = Annotated[RedisJSON, Depends(get_redis)]
QdrantDep = Annotated[AsyncQdrantClient, Depends(get_qdrant)]


async def get_raw_access_token(
    authorization: str | None = Header(default=None),
    orion_access: str | None = Cookie(default=None),
) -> str:
    """
    Resolve a bearer access token from the Authorization header or HTTP-only cookie.

    Args:
        authorization: Optional ``Authorization`` header value.
        orion_access: Optional cookie carrying the access JWT.

    Returns:
        Raw JWT string.

    Raises:
        UnauthorizedError: When no usable credential is present.
    """
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    if orion_access:
        return orion_access
    raise UnauthorizedError("Missing credentials")


def get_auth_service(
    session: DbSession,
    redis: RedisDep,
    settings: SettingsDep,
) -> AuthService:
    """Construct an AuthService with request-scoped dependencies."""
    return AuthService(session, redis, settings)


async def get_current_principal(
    session: DbSession,
    redis: RedisDep,
    settings: SettingsDep,
    token: Annotated[str, Depends(get_raw_access_token)],
) -> AuthPrincipal:
    """
    Validate the inbound access token and return the authenticated principal.

    Args:
        session: Database session.
        redis: Redis client.
        settings: Application settings.
        token: Raw JWT access token.

    Returns:
        Authenticated principal.

    Raises:
        UnauthorizedError: When the token is invalid or the user cannot authenticate.
    """
    service = AuthService(session, redis, settings)
    return await service.authenticate_access_token(token)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentPrincipal = Annotated[AuthPrincipal, Depends(get_current_principal)]


async def require_admin(principal: AuthPrincipal = Depends(get_current_principal)) -> AuthPrincipal:
    """
    Ensure the authenticated principal has an administrator role.

    Args:
        principal: Authenticated principal from upstream dependencies.

    Returns:
        The same principal when authorized.

    Raises:
        ForbiddenError: When the caller is not an admin.
    """
    if principal.role != UserRole.ADMIN:
        raise ForbiddenError("Administrator privileges are required for this operation")
    return principal


AdminPrincipal = Annotated[AuthPrincipal, Depends(require_admin)]


def get_document_service(
    session: DbSession,
    settings: SettingsDep,
    qdrant: QdrantDep,
) -> DocumentService:
    """Construct DocumentService with request-scoped clients."""
    return DocumentService(session, settings, qdrant)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
