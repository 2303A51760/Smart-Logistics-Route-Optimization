import sys
import os
from pathlib import Path
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# Ensure backend and root are in python path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_logistics.db"

import app.core.config as config_module
config_module.settings.ENVIRONMENT = "test"
config_module.settings.DATABASE_URL = "sqlite+aiosqlite:///./test_logistics.db"

import app.core.database as db_module
from app.core.database import Base
import app.models

from app.core.seed import seed_demo_data
from app.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test_logistics.db",
    echo=False,
    future=True,
    poolclass=NullPool,
)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Patch db_module engine and AsyncSessionLocal
db_module.engine = test_engine
db_module.AsyncSessionLocal = TestAsyncSessionLocal

async def override_get_db():
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[db_module.get_db] = override_get_db


def pytest_sessionstart(session):
    """Ensure clean database on test session start."""
    p = Path("./test_logistics.db")
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass


def pytest_sessionfinish(session, exitstatus):
    """Clean up test database on session finish."""
    p = Path("./test_logistics.db")
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass


@pytest_asyncio.fixture(autouse=True)
async def initialize_test_database():
    """Ensure database schema and demo seed data exist before running tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        await seed_demo_data(session)

    yield


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def admin_token_headers(async_client: AsyncClient):
    res = await async_client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Admin@123456"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def manager_token_headers(async_client: AsyncClient):
    res = await async_client.post("/api/v1/auth/login", json={"email": "manager@example.com", "password": "Manager@123456"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def driver_token_headers(async_client: AsyncClient):
    res = await async_client.post("/api/v1/auth/login", json={"email": "driver@example.com", "password": "Driver@123456"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
