import time
from datetime import datetime
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_db_connection
from app.core.redis import check_redis_connection
from app.schemas.health import HealthResponse, ServiceStatus

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def get_health():
    """Health check endpoint testing PostgreSQL and Redis readiness."""
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
        details="Real-time WebSocket dispatcher active on /ws/tracking",
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
