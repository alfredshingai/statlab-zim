"""API routers aggregation."""

from fastapi import APIRouter

from app.api.routes.health import router as health_router

api_router = APIRouter()

# Health at root and versioned prefix will be mounted in main.py separately;
# Keep api_router for future versioned routes (datasets, analyses, etc.)
api_router.include_router(health_router, prefix="/health", tags=["health"])

# Alternative: mount full health router under /api/v1 for versioned access
# This is handled via main.py duplication for Milestone 1 simplicity.

__all__ = ["api_router"]
