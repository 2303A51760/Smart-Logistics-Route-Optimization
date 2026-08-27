import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


import asyncio
import time

_db_alive_cache: tuple[bool, float] = (False, 0.0)


async def check_db_connection() -> bool:
    """Utility to test if database connection is alive with short timeout and caching."""
    global _db_alive_cache
    cached_status, last_checked = _db_alive_cache
    now = time.monotonic()
    # If checked within last 2.0 seconds, return cached status
    if now - last_checked < 2.0:
        return cached_status

    async def _ping():
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            return True

    try:
        is_alive = await asyncio.wait_for(_ping(), timeout=0.4)
        _db_alive_cache = (is_alive, now)
        return is_alive
    except Exception as e:
        logger.debug(f"Database check failed: {e}")
        _db_alive_cache = (False, now)
        return False

