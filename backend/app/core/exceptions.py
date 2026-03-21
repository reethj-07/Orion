"""Domain exceptions and FastAPI handlers producing a consistent API envelope."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.logging import get_logger
from app.schemas.common import APIResponse, ErrorDetail

logger = get_logger(__name__)


class OrionException(Exception):
    """Base application exception carrying HTTP status and machine-readable code."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "orion_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(OrionException):
    """Raised when a resource does not exist."""

    def __init__(self, message: str = "Resource not found", *, code: str = "not_found") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedError(OrionException):
    """Raised when authentication is missing or invalid."""

    def __init__(self, message: str = "Unauthorized", *, code: str = "unauthorized") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(OrionException):
    """Raised when the caller lacks permission."""

    def __init__(self, message: str = "Forbidden", *, code: str = "forbidden") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_403_FORBIDDEN)


class ConflictError(OrionException):
    """Raised when a unique constraint or business rule is violated."""

    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_409_CONFLICT)


class ValidationAppError(OrionException):
    """Raised for domain validation failures distinct from request schema errors."""

    def __init__(self, message: str, *, code: str = "validation_error") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


def _envelope_error(
    request: Request,
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_id = getattr(request.state, "request_id", None)
    body = APIResponse[None](
        success=False,
        data=None,
        error=ErrorDetail(code=code, message=message, details=details),
        meta={"request_id": request_id} if request_id else None,
    )
    return body.model_dump(exclude_none=True)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    @app.exception_handler(OrionException)
    async def orion_exception_handler(request: Request, exc: OrionException) -> JSONResponse:
        logger.warning(
            "orion_exception",
            code=exc.code,
            message=exc.message,
            path=str(request.url.path),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope_error(
                request,
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.info("validation_error", errors=exc.errors(), path=str(request.url.path))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope_error(
                request,
                code="request_validation_error",
                message="Request validation failed",
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        logger.info("rate_limit_exceeded", path=str(request.url.path))
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=_envelope_error(
                request,
                code="rate_limited",
                message=str(exc.detail),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=str(request.url.path), exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope_error(
                request,
                code="internal_error",
                message="An unexpected error occurred",
            ),
        )
