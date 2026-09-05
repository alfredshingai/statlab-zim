"""Health-check endpoint — Milestone 1.

Provides:
- GET /health
- GET /api/v1/health (versioned alias)
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    service: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health, version and environment. Used by load balancers and monitoring.",
    response_description="Health status payload",
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        service=settings.PROJECT_NAME,
    )


# Example endpoint for Milestone 1 demonstration
class PingResponse(BaseModel):
    message: str
    version: str


@router.get(
    "/ping",
    response_model=PingResponse,
    summary="Ping",
    description="Simple liveness probe returning a message.",
)
async def ping(settings: Settings = Depends(get_settings)) -> PingResponse:
    return PingResponse(message="pong", version=settings.VERSION)
