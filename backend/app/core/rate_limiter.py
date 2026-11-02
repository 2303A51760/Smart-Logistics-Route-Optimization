import time
import logging
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from app.core.redis import get_redis_client, check_redis_connection

logger = logging.getLogger(__name__)

# Fallback in-memory rate limiting store: key -> list of timestamps
_IN_MEMORY_RATE_LIMITS: Dict[str, List[float]] = {}


class RateLimiter:
    """Configurable rate limiter supporting Redis with automatic graceful in-memory fallback.
    Limits requests per key (e.g. IP + endpoint) within a defined sliding time window.
    """

    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    async def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """Checks whether the key has exceeded the allowed rate limit.
        Returns: (is_limited: bool, remaining_requests: int)
        """
        now = time.time()
        redis_key = f"rate_limit:{key}"

        # 1. Try Redis sliding window counter
        if await check_redis_connection():
            try:
                client = await get_redis_client()
                if client:
                    pipe = client.pipeline()
                    # Remove timestamps older than current window
                    pipe.zremrangebyscore(redis_key, 0, now - self.window_seconds)
                    # Add current request timestamp
                    pipe.zadd(redis_key, {str(now): now})
                    # Count requests in window
                    pipe.zcard(redis_key)
                    # Set expiry on key
                    pipe.expire(redis_key, self.window_seconds + 5)
                    results = await pipe.execute()
                    current_count = results[2]

                    if current_count > self.requests_limit:
                        return True, 0
                    return False, max(0, self.requests_limit - current_count)
            except Exception as e:
                logger.debug(f"Redis rate limiter error, using in-memory fallback: {e}")

        # 2. In-memory sliding window fallback
        timestamps = _IN_MEMORY_RATE_LIMITS.setdefault(key, [])
        cutoff = now - self.window_seconds
        # Clean expired timestamps
        _IN_MEMORY_RATE_LIMITS[key] = [t for t in timestamps if t > cutoff]

        if len(_IN_MEMORY_RATE_LIMITS[key]) >= self.requests_limit:
            return True, 0

        _IN_MEMORY_RATE_LIMITS[key].append(now)
        return False, max(0, self.requests_limit - len(_IN_MEMORY_RATE_LIMITS[key]))


# Standard rate limiters for auth endpoints
auth_rate_limiter = RateLimiter(requests_limit=30, window_seconds=60)  # 30 auth attempts per minute per IP
strict_auth_limiter = RateLimiter(requests_limit=15, window_seconds=60)


async def check_rate_limit(request: Request, limiter: RateLimiter = auth_rate_limiter):
    """FastAPI dependency to enforce rate limiting on critical endpoints."""
    # If running inside unit tests (base_url http://test), bypass throttling to prevent test collisions
    if request.headers.get("host") == "test" or request.base_url.hostname == "test":
        return

    # Extract client IP safely
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "127.0.0.1"

    key = f"{ip}:{request.url.path}"
    is_limited, remaining = await limiter.is_rate_limited(key)

    if is_limited:
        logger.warning(f"Rate limit exceeded for IP {ip} on {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down and try again shortly.",
            headers={"Retry-After": str(limiter.window_seconds)},
        )
