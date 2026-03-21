"""Authenticated principal attached to requests after token validation."""

from dataclasses import dataclass
from uuid import UUID

from app.models.user import UserRole


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    """
    Lightweight identity used by route handlers and services.

    Attributes:
        user_id: Authenticated user identifier.
        org_id: Owning organization identifier.
        email: Normalized email address.
        role: Authorization role for the user.
    """

    user_id: UUID
    org_id: UUID
    email: str
    role: UserRole
