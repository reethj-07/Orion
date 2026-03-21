"""Authentication-related request and response schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    """Payload for self-service registration of an organization admin."""

    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    organization_name: str = Field(..., min_length=2, max_length=255)


class LoginRequest(BaseModel):
    """Payload for password-based login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenPair(BaseModel):
    """Access and refresh tokens returned to API clients."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    """Non-sensitive user projection for authenticated responses."""

    id: UUID
    email: EmailStr
    role: UserRole
    org_id: UUID
    is_active: bool


class AuthResponse(BaseModel):
    """Combined token and user payload after login or registration."""

    tokens: TokenPair
    user: UserPublic


class RefreshRequest(BaseModel):
    """Optional body refresh payload when cookies are not used."""

    refresh_token: str | None = Field(
        default=None,
        description="Refresh token when not provided via cookie.",
    )


class MessageResponse(BaseModel):
    """Simple textual status response."""

    message: str
