"""Rate limiting middleware using Redis sliding window."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis.

    Args:
        app: ASGI application.
        redis_url: Redis connection URL.
        max_requests: Maximum requests per window.
        window_seconds: Window duration in seconds.
    """

    def __init__(
        self,
        app,
        redis_url: str = "redis://localhost:6379/0",
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self._redis_url = redis_url
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._redis = None

    async def _get_redis(self):
        """Lazy-init async Redis connection.

        Returns:
            Redis client instance or None if unavailable.
        """
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            except Exception as exc:
                logger.warning("Rate limiter: Redis unavailable: %s", exc)
                return None
        return self._redis

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check rate limit before passing request to handler.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response or 429 if rate limited.
        """
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/readiness"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        redis = await self._get_redis()

        if redis is None:
            # Fail open if Redis is unavailable
            return await call_next(request)

        key = f"rate_limit:{client_ip}"
        now = time.time()
        window_start = now - self._window_seconds

        try:
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self._window_seconds)
            results = await pipe.execute()
            request_count = results[2]
        except Exception as exc:
            logger.warning("Rate limiter error: %s", exc)
            return await call_next(request)

        if request_count > self._max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "code": "RATE_LIMITED",
                },
                headers={
                    "Retry-After": str(self._window_seconds),
                    "X-RateLimit-Limit": str(self._max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        remaining = max(0, self._max_requests - request_count)
        response.headers["X-RateLimit-Limit"] = str(self._max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
