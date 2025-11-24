"""Rate limiting middleware using Redis"""

import time
from typing import Callable

from fastapi import Request, Response, status
from opentelemetry import trace
from redis import Redis

from app.config import get_settings

settings = get_settings()
tracer = trace.get_tracer(__name__)


class RateLimitMiddleware:
    """Middleware for rate limiting using Redis"""

    def __init__(self, app: Callable, redis_client: Redis):
        self.app = app
        self.redis = redis_client
        self.enabled = settings.rate_limit_enabled
        self.per_minute = settings.rate_limit_requests_per_minute
        self.per_hour = settings.rate_limit_requests_per_hour

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Process request with rate limiting"""

        if not self.enabled:
            await self.app(scope, receive, send)
            return

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"

        with tracer.start_as_current_span("rate_limit_check") as span:
            span.set_attribute("client_ip", client_ip)
            span.set_attribute("path", request.url.path)

            # Check rate limits
            minute_key = f"rate_limit:minute:{client_ip}"
            hour_key = f"rate_limit:hour:{client_ip}"

            current_minute = int(time.time() / 60)
            current_hour = int(time.time() / 3600)

            minute_count = self.redis.get(f"{minute_key}:{current_minute}")
            hour_count = self.redis.get(f"{hour_key}:{current_hour}")

            minute_count = int(minute_count) if minute_count else 0
            hour_count = int(hour_count) if hour_count else 0

            span.set_attribute("rate_limit.minute.count", minute_count)
            span.set_attribute("rate_limit.hour.count", hour_count)

            if minute_count >= self.per_minute:
                span.set_attribute("rate_limit.exceeded", "minute")
                response = Response(
                    content="Rate limit exceeded: too many requests per minute",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                )
                await response(scope, receive, send)
                return

            if hour_count >= self.per_hour:
                span.set_attribute("rate_limit.exceeded", "hour")
                response = Response(
                    content="Rate limit exceeded: too many requests per hour",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                )
                await response(scope, receive, send)
                return

            # Increment counters
            pipe = self.redis.pipeline()
            pipe.incr(f"{minute_key}:{current_minute}")
            pipe.expire(f"{minute_key}:{current_minute}", 60)
            pipe.incr(f"{hour_key}:{current_hour}")
            pipe.expire(f"{hour_key}:{current_hour}", 3600)
            pipe.execute()

            await self.app(scope, receive, send)

