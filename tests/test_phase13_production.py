import pytest
from httpx import AsyncClient


# ==========================================
# 1. HEALTH AND READINESS OBSERVABILITY
# ==========================================
@pytest.mark.asyncio
async def test_root_health_and_api_v1_health(async_client: AsyncClient):
    # Root /health
    res_root = await async_client.get("/health")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert "status" in data_root
    assert data_root["status"] in ("healthy", "degraded")
    assert "services" in data_root
    assert "database" in data_root["services"]
    assert "redis" in data_root["services"]

    # API v1 /api/v1/health
    res_v1 = await async_client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["app_name"] is not None


@pytest.mark.asyncio
async def test_readiness_probe_endpoints(async_client: AsyncClient):
    # Root /ready
    res_root = await async_client.get("/ready")
    assert res_root.status_code in (200, 503)
    data_root = res_root.json()
    assert "status" in data_root
    assert "database" in data_root
    assert "redis" in data_root

    # API v1 /api/v1/health/ready
    res_v1 = await async_client.get("/api/v1/health/ready")
    assert res_v1.status_code in (200, 503)


# ==========================================
# 2. OPERATIONAL METRICS ENDPOINT
# ==========================================
@pytest.mark.asyncio
async def test_operational_metrics_endpoint(async_client: AsyncClient):
    # Trigger a request first
    await async_client.get("/")

    # Root /metrics
    res = await async_client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0
    assert "total_requests" in data
    assert data["total_requests"] >= 1
    assert "error_requests" in data
    assert data["system_status"] == "operational"

    # API v1 /api/v1/health/metrics
    res_v1 = await async_client.get("/api/v1/health/metrics")
    assert res_v1.status_code == 200
    assert res_v1.json()["total_requests"] >= 1


# ==========================================
# 3. REQUEST CORRELATION ID PROPAGATION
# ==========================================
@pytest.mark.asyncio
async def test_request_id_generation_and_propagation(async_client: AsyncClient):
    # 1. Without custom request ID -> auto-generated
    res_auto = await async_client.get("/")
    assert res_auto.status_code == 200
    assert "X-Request-ID" in res_auto.headers
    assert len(res_auto.headers["X-Request-ID"]) > 0

    # 2. With custom incoming request ID -> preserved in response
    custom_id = "trace-client-alpha-998811"
    res_custom = await async_client.get("/", headers={"X-Request-ID": custom_id})
    assert res_custom.status_code == 200
    assert res_custom.headers.get("X-Request-ID") == custom_id


# ==========================================
# 4. SECURITY HEADERS VALIDATION
# ==========================================
@pytest.mark.asyncio
async def test_production_security_headers(async_client: AsyncClient):
    res = await async_client.get("/")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "1; mode=block" in headers.get("X-XSS-Protection", "")
    assert "max-age=" in headers.get("Strict-Transport-Security", "")


# ==========================================
# 5. SAFE GLOBAL ERROR HANDLING
# ==========================================
@pytest.mark.asyncio
async def test_error_handling_sanitization(async_client: AsyncClient):
    # Requesting non-existent endpoint returns 404 with standard detail
    res_404 = await async_client.get("/api/v1/nonexistent-route-endpoint-xyz")
    assert res_404.status_code == 404
    assert "detail" in res_404.json()
    assert "X-Request-ID" in res_404.headers


# ==========================================
# 6. CORS CONFIGURATION INTEGRITY
# ==========================================
@pytest.mark.asyncio
async def test_cors_headers_handling(async_client: AsyncClient):
    res = await async_client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    # Status code should be 200 OK for OPTIONS preflight
    assert res.status_code == 200


# ==========================================
# 7. PRODUCTION SECURITY HARDENING VALIDATION
# ==========================================
def test_production_security_refuses_default_secrets():
    """Verify system refuses to start in production if secrets are placeholder or default."""
    from app.core.config import Settings

    # 1. Default SECRET_KEY in production raises error
    with pytest.raises(ValueError, match="SECRET_KEY must be set to a cryptographically secure random string"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="dev-insecure-secret-key-for-local-testing-only-32chars",
            JWT_SECRET_KEY="a_strong_jwt_secret_key_with_over_32_characters_123456",
            POSTGRES_PASSWORD="secure_strong_database_password_999",
            _env_file=None,
        )

    # 2. Default JWT_SECRET_KEY in production raises error
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be set to a cryptographically secure random string"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a_strong_secret_key_with_over_32_characters_1234567890",
            JWT_SECRET_KEY="supersecret-jwt-key-change-in-production-smart-logistics",
            POSTGRES_PASSWORD="secure_strong_database_password_999",
            _env_file=None,
        )

    # 3. Default POSTGRES_PASSWORD in production raises error
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD cannot be default"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a_strong_secret_key_with_over_32_characters_1234567890",
            JWT_SECRET_KEY="a_strong_jwt_secret_key_with_over_32_characters_123456",
            POSTGRES_PASSWORD="postgres",
            _env_file=None,
        )

    # 4. Valid strong production configuration succeeds
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a_strong_secret_key_with_over_32_characters_1234567890",
        JWT_SECRET_KEY="a_strong_jwt_secret_key_with_over_32_characters_123456",
        POSTGRES_PASSWORD="secure_strong_database_password_999",
        _env_file=None,
    )
    assert prod_settings.ENVIRONMENT == "production"


def test_docker_entrypoint_environment_guard():
    """Verify entrypoint script only auto-migrates and seeds in development or test, never production."""
    from pathlib import Path
    entrypoint_path = Path("docker/entrypoint.sh")
    assert entrypoint_path.exists(), "docker/entrypoint.sh must exist"
    content = entrypoint_path.read_text(encoding="utf-8")
    assert '[ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "test" ]' in content
    assert "Skipping automatic dev migrations and seeding" in content
