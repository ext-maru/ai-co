import time
from typing import Optional

import redis
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with Redis backend"""

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client or redis.from_url(settings.REDIS_URL)
        self.default_rate_limit = settings.RATE_LIMIT_REQUESTS
        self.default_window = settings.RATE_LIMIT_WINDOW

        # Different rate limits for different user roles
        self.role_limits = {
            "grand_elder": {"requests": 1000, "window": 900},
            "elder": {"requests": 500, "window": 900},
            "sage": {"requests": 200, "window": 900},
            "servant": {"requests": 100, "window": 900},
            "anonymous": {"requests": 20, "window": 900},
        }

        # Endpoint-specific rate limits
        self.endpoint_limits = {
            "/api/v1/auth/login": {"requests": 5, "window": 300},  # 5 attempts per 5 minutes
            "/api/v1/auth/register": {"requests": 3, "window": 3600},  # 3 registrations per hour
            "/api/v1/sages/search": {"requests": 50, "window": 60},  # 50 searches per minute
            "/ws": {"requests": 10, "window": 60},  # 10 WebSocket connections per minute
        }

    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = self.get_client_id(request)

        # Get user role from token if available
        user_role = await self.get_user_role(request)

        # Check rate limit
        if not await self.check_rate_limit(request, client_id, user_role):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": self.get_retry_after(client_id, user_role),
                },
                headers={
                    "Retry-After": str(self.get_retry_after(client_id, user_role)),
                    "X-RateLimit-Limit": str(self.get_rate_limit(user_role, request.url.path)),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Record request
        await self.record_request(request, client_id, user_role)

        response = await call_next(request)

        # Add rate limit headers
        remaining = await self.get_remaining_requests(client_id, user_role, request.url.path)
        response.headers["X-RateLimit-Limit"] = str(self.get_rate_limit(user_role, request.url.path))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.get_window(user_role, request.url.path))

        return response

    def get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get user ID from token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from ..core.security import security_manager

                token = auth_header.split(" ")[1]
                payload = security_manager.verify_token(token)
                if payload:
                    return f"user:{payload.get('sub')}"
            except:
                pass

        # Fall back to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        return f"ip:{request.client.host}"

    async def get_user_role(self, request: Request) -> str:
        """Extract user role from JWT token"""
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from ..core.security import security_manager

                token = auth_header.split(" ")[1]
                payload = security_manager.verify_token(token)
                if payload:
                    return payload.get("role", "servant")
            except:
                pass

        return "anonymous"

    def get_rate_limit(self, user_role: str, endpoint: str) -> int:
        """Get rate limit for user role and endpoint"""
        # Check endpoint-specific limits first
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]["requests"]

        # Use role-based limits
        return self.role_limits.get(user_role, self.role_limits["anonymous"])["requests"]

    def get_window(self, user_role: str, endpoint: str) -> int:
        """Get time window for rate limit"""
        # Check endpoint-specific limits first
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]["window"]

        # Use role-based limits
        return self.role_limits.get(user_role, self.role_limits["anonymous"])["window"]

    async def check_rate_limit(self, request: Request, client_id: str, user_role: str) -> bool:
        """Check if request is within rate limit"""
        endpoint = request.url.path
        rate_limit = self.get_rate_limit(user_role, endpoint)
        window = self.get_window(user_role, endpoint)

        key = f"rate_limit:{client_id}:{endpoint}"
        current_time = int(time.time())
        window_start = current_time - window

        try:
            # Use Redis sliding window
            pipe = self.redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            pipe.zcard(key)

            # Add current request timestamp
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration
            pipe.expire(key, window)

            results = pipe.execute()
            current_requests = results[1]

            return current_requests < rate_limit

        except Exception as e:
            # If Redis is unavailable, allow the request
            print(f"Rate limit check failed: {e}")
            return True

    async def record_request(self, request: Request, client_id: str, user_role: str):
        """Record request for rate limiting"""
        endpoint = request.url.path
        key = f"rate_limit:{client_id}:{endpoint}"
        current_time = int(time.time())

        try:
            self.redis_client.zadd(key, {str(current_time): current_time})
        except Exception as e:
            print(f"Failed to record request: {e}")

    async def get_remaining_requests(self, client_id: str, user_role: str, endpoint: str) -> int:
        """Get remaining requests for client"""
        rate_limit = self.get_rate_limit(user_role, endpoint)
        window = self.get_window(user_role, endpoint)

        key = f"rate_limit:{client_id}:{endpoint}"
        current_time = int(time.time())
        window_start = current_time - window

        try:
            # Clean old entries and count current
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = pipe.execute()

            current_requests = results[1]
            return max(0, rate_limit - current_requests)

        except Exception:
            return rate_limit

    def get_retry_after(self, client_id: str, user_role: str) -> int:
        """Get retry after time in seconds"""
        return self.get_window(user_role, "")


class IPWhitelist:
    """IP whitelist for trusted sources"""

    def __init__(self, whitelist: list = None):
        self.whitelist = whitelist or ["127.0.0.1", "::1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        return ip in self.whitelist


class DDoSProtection:
    """DDoS protection middleware"""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.threshold = 100  # requests per minute
        self.block_duration = 3600  # 1 hour

    async def check_ddos(self, request: Request) -> bool:
        """Check for potential DDoS attack"""
        client_ip = request.client.host
        key = f"ddos:{client_ip}"
        current_time = int(time.time())
        minute_ago = current_time - 60

        try:
            # Count requests in last minute
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, minute_ago)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, 3600)

            results = pipe.execute()
            requests_count = results[1]

            if requests_count > self.threshold:
                # Block IP
                block_key = f"blocked:{client_ip}"
                self.redis_client.setex(block_key, self.block_duration, "blocked")
                return False

            return True

        except Exception:
            return True

    async def is_blocked(self, request: Request) -> bool:
        """Check if IP is blocked"""
        client_ip = request.client.host
        block_key = f"blocked:{client_ip}"

        try:
            return self.redis_client.exists(block_key)
        except Exception:
            return False
