"""Admin API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import UserRole
from app.schemas.auth import UserPublic


class APIKeyCreateRequest(BaseModel):
    """Request body for minting a new API key."""

    scopes: list[str] = Field(default_factory=lambda: ["read", "write"])
    expires_at: datetime | None = None


class APIKeyCreatedResponse(BaseModel):
    """Response containing the raw secret exactly once."""

    id: UUID
    secret: str
    scopes: list[str]
    expires_at: datetime | None


class APIKeySummary(BaseModel):
    """Non-sensitive API key metadata."""

    id: UUID
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime


class UserRoleUpdateRequest(BaseModel):
    """Payload for updating a user's role."""

    role: UserRole
