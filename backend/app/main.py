"""FastAPI application — StatLab Zim Backend (Milestone 1).

Features:
- Health-check endpoint: GET /health
- API documentation: /docs (Swagger), /redoc, /openapi.json
- Configuration via environment variables (.env + pydantic-settings)
- CORS support
- Basic error handling (HTTPException, validation, generic)
- Structured logging scaffold
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.health import router as health_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.reports import router as reports_router
from app.api.routes.ai import router as ai_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger("statlab")

# Lifespan for startup/shutdown hooks (reserved for DB connections later)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} env={settings.ENVIRONMENT}")
    # Milestone 3: ensure tables exist (SQLite dev); in prod use alembic
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"DB init failed: {e}")
    yield
    logger.info("Shutting down StatLab Zim API")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION + "\n\n**Milestone 1:** Backend foundation.\n**Milestone 2:** Statistical API.\n**Milestone 3:** Database.\n**Milestone 5:** Auth.\n**Milestone 7:** Reports.\n**Version 3:** AI StatLab — ask/suggest/explain/cleaning (verified Python → AI explanation).",


        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware (basic observability)
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        process_time = time.time() - start
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # --- Error handlers ---
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "status_code": 422,
                "detail": exc.errors(),
                "body": str(exc.body) if hasattr(exc, "body") else None,
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled error on {request.url.path}: {exc}")
        # Don't leak internals in production
        detail = str(exc) if settings.DEBUG else "Internal server error"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "status_code": 500,
                "detail": detail,
                "path": request.url.path,
            },
        )

    # --- Routes ---
    # Health at root (GET /health) and versioned (GET /api/v1/health)
    app.include_router(health_router, tags=["health"])
    app.include_router(health_router, prefix=settings.API_V1_STR, tags=["health"])
    # Milestone 2 — Statistical API
    app.include_router(datasets_router, tags=["datasets"])
    app.include_router(datasets_router, prefix=settings.API_V1_STR, tags=["datasets"])
    app.include_router(analyses_router, tags=["analyses"])
    app.include_router(analyses_router, prefix=settings.API_V1_STR, tags=["analyses"])
    # Milestone 5 & 7 — Auth, Projects, Reports
    app.include_router(auth_router, tags=["auth"])
    app.include_router(auth_router, prefix=settings.API_V1_STR, tags=["auth"])
    app.include_router(projects_router, tags=["projects"])
    app.include_router(projects_router, prefix=settings.API_V1_STR, tags=["projects"])
    app.include_router(reports_router, tags=["reports"])
    app.include_router(reports_router, prefix=settings.API_V1_STR, tags=["reports"])
    # Version 3 — AI StatLab
    app.include_router(ai_router, tags=["ai"])
    app.include_router(ai_router, prefix=settings.API_V1_STR, tags=["ai"])

    @app.get(
        "/",
        tags=["root"],
        summary="Root",
        description="Welcome endpoint with service info and docs links.",
    )
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": "/docs",
            "health": "/health",
            "health_versioned": f"{settings.API_V1_STR}/health",
            "datasets_upload": "/datasets/upload",
            "analyses": "/analyses",
            "auth": "/auth",
            "projects": "/projects",
            "reports": "/reports",
            "ai": "/ai",
        }

    return app


app = create_app()
