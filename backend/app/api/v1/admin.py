"""Administrative routes for org-level management."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.responses import success_envelope
from app.core.dependencies import AdminPrincipal, DbSession
from app.schemas.admin import (
    APIKeyCreatedResponse,
    APIKeyCreateRequest,
    APIKeySummary,
    UserRoleUpdateRequest,
)
from app.schemas.auth import UserPublic
from app.schemas.common import APIResponse
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/users", response_model=APIResponse[list[UserPublic]])
async def list_org_users(
    request: Request,
    principal: AdminPrincipal,
    session: DbSession,
) -> APIResponse[list[UserPublic]]:
    """
    List users that belong to the administrator's organization.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated administrator principal.
        session: Database session.

    Returns:
        API envelope with user projections.
    """
    service = AdminService(session)
    users = await service.list_users(principal)
    return success_envelope(request, users)


@router.patch("/users/{user_id}/role", response_model=APIResponse[UserPublic])
async def update_user_role(
    request: Request,
    principal: AdminPrincipal,
    session: DbSession,
    user_id: UUID,
    payload: UserRoleUpdateRequest,
) -> APIResponse[UserPublic]:
    """
    Update a member's role within the organization.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated administrator principal.
        session: Database session.
        user_id: Target user identifier.
        payload: Role update body.

    Returns:
        API envelope with the updated user projection.
    """
    service = AdminService(session)
    updated = await service.update_user_role(principal, user_id, payload.role)
    return success_envelope(request, updated)


@router.post("/api-keys", response_model=APIResponse[APIKeyCreatedResponse])
async def create_api_key(
    request: Request,
    principal: AdminPrincipal,
    session: DbSession,
    payload: APIKeyCreateRequest,
) -> APIResponse[APIKeyCreatedResponse]:
    """
    Mint a new API key for programmatic access.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated administrator principal.
        session: Database session.
        payload: API key creation body.

    Returns:
        API envelope containing the raw secret once.
    """
    service = AdminService(session)
    created = await service.create_api_key(principal, payload)
    return success_envelope(request, created)


@router.get("/api-keys", response_model=APIResponse[list[APIKeySummary]])
async def list_api_keys(
    request: Request,
    principal: AdminPrincipal,
    session: DbSession,
) -> APIResponse[list[APIKeySummary]]:
    """
    List API key metadata without revealing secrets.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated administrator principal.
        session: Database session.

    Returns:
        API envelope with API key summaries.
    """
    service = AdminService(session)
    keys = await service.list_api_keys(principal)
    return success_envelope(request, keys)
