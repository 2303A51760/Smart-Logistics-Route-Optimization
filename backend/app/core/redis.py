import asyncio
import json
import logging
import time
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: Optional[aioredis.Redis] = None
_redis_alive_cache: tuple[bool, float] = (False, 0.0)
REDIS_TRACKING_CHANNEL = "tracking:driver_updates"


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Provides singleton async Redis client with graceful failure handling."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")
            redis_client = None
    return redis_client


async def check_redis_connection() -> bool:
    """Utility to test if Redis connection is alive with short timeout & caching."""
    if getattr(settings, "ENVIRONMENT", "").lower() in ("test", "testing"):
        return False

    global _redis_alive_cache
    cached_status, last_checked = _redis_alive_cache
    now = time.monotonic()
    if now - last_checked < 3.0:
        return cached_status

    try:
        client = await get_redis_client()
        if client:
            alive = await asyncio.wait_for(client.ping(), timeout=0.5)
            _redis_alive_cache = (alive, now)
            return alive
        _redis_alive_cache = (False, now)
        return False
    except Exception as e:
        logger.debug(f"Redis check failed: {e}")
        _redis_alive_cache = (False, now)
        return False


async def publish_tracking_event(event_data: dict) -> bool:
    """
    Publish real-time tracking event to Redis channel.
    Returns True if published to Redis, False if Redis is unavailable (degraded mode).
    """
    try:
        client = await get_redis_client()
        if client:
            payload = json.dumps(event_data, default=str)
            await client.publish(REDIS_TRACKING_CHANNEL, payload)
            return True
        return False
    except Exception as e:
        logger.warning(f"Redis publish failed (falling back to degraded local distribution): {e}")
        return False


async def close_redis_connection():
    """Close Redis client connection on shutdown."""
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
        except Exception as e:
            logger.debug(f"Error closing Redis connection: {e}")
        redis_client = None
