"""Shared API envelope models used across versioned routes."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error payload returned to API clients."""

    code: str = Field(..., description="Stable machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    details: dict[str, Any] | None = Field(default=None, description="Optional structured details.")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response envelope.

    All successful and error responses use this shape for consistency.
    """

    success: bool = Field(..., description="Whether the operation succeeded.")
    data: T | None = Field(default=None, description="Response payload on success.")
    error: ErrorDetail | None = Field(default=None, description="Error payload on failure.")
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Metadata such as request_id or pagination hints.",
    )
