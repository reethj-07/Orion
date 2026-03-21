"""Helpers for building consistent API envelopes."""

from typing import Any, TypeVar
from uuid import UUID

from fastapi import Request

from app.schemas.common import APIResponse

T = TypeVar("T")


def success_envelope(request: Request, data: T, meta: dict[str, Any] | None = None) -> APIResponse[T]:
    """
    Build a successful API envelope including request correlation metadata.

    Args:
        request: Active HTTP request.
        data: Response payload.
        meta: Optional extra metadata merged on top of request_id.

    Returns:
        Typed APIResponse with success=True.
    """
    request_id = getattr(request.state, "request_id", None)
    merged: dict[str, Any] = {}
    if request_id is not None:
        merged["request_id"] = str(request_id)
    if meta:
        merged.update(meta)
    return APIResponse[T](success=True, data=data, error=None, meta=merged or None)


def pagination_meta(*, total: int, page: int, page_size: int) -> dict[str, Any]:
    """
    Build standard pagination metadata for list endpoints.

    Args:
        total: Total matching rows.
        page: Current page index (1-based).
        page_size: Page size.

    Returns:
        Metadata dictionary suitable for the API envelope meta field.
    """
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max((total + page_size - 1) // page_size, 1),
    }


def uuid_to_str(value: UUID | str | None) -> str | None:
    """Normalize UUID-like values to canonical string form."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    return str(UUID(value))
