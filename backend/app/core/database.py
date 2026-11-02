import asyncio
import logging
import time
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Configure engine arguments with connection pooling for PostgreSQL
engine_kwargs = {
    "echo": False,
    "future": True,
    "pool_pre_ping": True,
}

if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update({
        "pool_size": settings.POSTGRES_POOL_SIZE,
        "max_overflow": settings.POSTGRES_MAX_OVERFLOW,
        "pool_timeout": settings.POSTGRES_POOL_TIMEOUT,
        "pool_recycle": settings.POSTGRES_POOL_RECYCLE,
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

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


async def close_db_connection():
    """Disposes engine connection pool gracefully on shutdown."""
    try:
        await engine.dispose()
        logger.info("Database connection pool disposed.")
    except Exception as e:
        logger.debug(f"Error disposing database pool: {e}")


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
        is_alive = await asyncio.wait_for(_ping(), timeout=0.5)
        _db_alive_cache = (is_alive, now)
        return is_alive
    except Exception as e:
        logger.debug(f"Database check failed: {e}")
        _db_alive_cache = (False, now)
        return False
