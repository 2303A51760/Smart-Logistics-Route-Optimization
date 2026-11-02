import sys
import uuid
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root and backend directories are in sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
_BACKEND_DIR = str(Path(__file__).resolve().parents[1])
for _p in [_PROJECT_ROOT, _BACKEND_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, set_request_id, get_request_id
from app.core.redis import close_redis_connection
from app.core.database import close_db_connection
from app.core.metrics import increment_request_count, increment_error_count
from app.api.v1.api import api_router
from app.api.websockets.tracking import ws_router
from app.api.v1.endpoints.health import get_health, get_readiness, get_metrics

# Initialize structured logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown hooks."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT})")
    if getattr(settings, "ENVIRONMENT", "").lower() in ("development", "test", "testing"):
        try:
            from app.core.database import AsyncSessionLocal
            from app.core.seed import seed_demo_data
            async with AsyncSessionLocal() as session:
                await seed_demo_data(session)
        except Exception as e:
            logger.warning(f"Could not automatically seed demo data on startup: {e}")
    yield
    logger.info("Shutting down resources...")
    await close_redis_connection()
    await close_db_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="High-performance backend API for Route Optimization, Fleet Telemetry, and Delivery Management.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if settings.BACKEND_CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Request Correlation ID & Latency Logging Middleware
@app.middleware("http")
async def request_correlation_middleware(request: Request, call_next):
    """Assigns or propagates X-Request-ID and tracks request lifecycle."""
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
    set_request_id(request_id)
    increment_request_count()

    t0 = time.perf_counter()
    try:
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # Log request completion
        if not request.url.path.startswith("/health"):
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
            )
        return response
    except Exception as exc:
        increment_error_count()
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path} ({duration_ms}ms): {exc}",
            exc_info=True,
        )
        raise exc


# 3. Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Adds enterprise HTTP security headers to all HTTP responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# 4. Global Exception Handlers
@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    """Safe global error handler preventing stack trace or credential leakage in production."""
    increment_error_count()
    req_id = get_request_id() or "unknown"
    logger.error(f"Global error on {request.method} {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error. Please contact system support.",
            "request_id": req_id,
        },
        headers={"X-Request-ID": req_id},
    )


# 5. Include API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)


# 6. Top-level Observability & Health Routes
@app.get("/health", tags=["Observability"])
async def root_health():
    """Top-level health check endpoint."""
    return await get_health()


@app.get("/ready", tags=["Observability"])
async def root_ready(response: Response):
    """Top-level readiness probe endpoint."""
    return await get_readiness(response)


@app.get("/metrics", tags=["Observability"])
async def root_metrics():
    """Top-level operational metrics endpoint."""
    return await get_metrics()


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "ready": "/ready",
        "metrics": "/metrics",
    }
