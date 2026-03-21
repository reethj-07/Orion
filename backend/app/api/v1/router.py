"""Aggregate router for API v1."""

from fastapi import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.v1 import admin as admin_routes
from app.api.v1 import analytics as analytics_routes
from app.api.v1 import auth as auth_routes
from app.api.v1 import documents as document_routes
from app.api.v1 import search as search_routes
from app.api.v1 import workflows as workflow_routes
from app.core.config import get_settings

_settings = get_settings()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_settings.rate_limit_default],
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
api_router.include_router(document_routes.router, prefix="/documents", tags=["documents"])
api_router.include_router(workflow_routes.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(search_routes.router, prefix="/search", tags=["search"])
api_router.include_router(analytics_routes.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin_routes.router, prefix="/admin", tags=["admin"])
