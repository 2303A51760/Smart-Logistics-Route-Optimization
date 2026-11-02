import time
from datetime import datetime
from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.core.database import check_db_connection
from app.core.redis import check_redis_connection
from app.core.metrics import get_metrics_data
from app.schemas.health import HealthResponse, ServiceStatus, ReadinessResponse, MetricsResponse
from app.api.websockets.tracking import tracking_manager as ws_manager

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def get_health():
    """Health check endpoint testing PostgreSQL and Redis status."""
    services = {}

    # Check Database
    t0 = time.perf_counter()
    db_ok = await check_db_connection()
    db_latency = (time.perf_counter() - t0) * 1000
    services["database"] = ServiceStatus(
        status="healthy" if db_ok else "unreachable",
        latency_ms=round(db_latency, 2) if db_ok else None,
        details=f"PostgreSQL @ {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}" if db_ok else "Could not connect to PostgreSQL server",
    )

    # Check Redis
    t0 = time.perf_counter()
    redis_ok = await check_redis_connection()
    redis_latency = (time.perf_counter() - t0) * 1000
    services["redis"] = ServiceStatus(
        status="healthy" if redis_ok else "unreachable",
        latency_ms=round(redis_latency, 2) if redis_ok else None,
        details=f"Redis @ {settings.REDIS_HOST}:{settings.REDIS_PORT}" if redis_ok else "Could not connect to Redis server",
    )

    # WebSockets service
    services["websockets"] = ServiceStatus(
        status="healthy",
        latency_ms=0.1,
        details=f"Real-time WebSocket dispatcher active ({len(ws_manager.active_connections)} active)",
    )

    overall_status = "healthy" if (db_ok and redis_ok) else "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        services=services,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/ready", response_model=ReadinessResponse)
async def get_readiness(response: Response):
    """Readiness probe verifying core backend and database readiness."""
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()

    # In degraded mode (e.g. Redis offline or SQLite fallback), the service is still operational
    # However if DB is down when required, we return 503 Service Unavailable
    is_ready = True
    if not db_ok and "postgresql" in settings.DATABASE_URL:
        is_ready = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        database="healthy" if db_ok else "unreachable",
        redis="healthy" if redis_ok else "degraded",
        app="ready",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Safe operational metrics endpoint."""
    m = get_metrics_data()
    return MetricsResponse(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        uptime_seconds=m["uptime_seconds"],
        total_requests=m["total_requests"],
        error_requests=m["error_requests"],
        active_websockets=len(ws_manager.active_connections),
        system_status=m["system_status"],
        timestamp=m["timestamp"],
    )
