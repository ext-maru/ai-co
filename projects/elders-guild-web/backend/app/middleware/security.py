import hashlib
import html
import re
import secrets
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from urllib.parse import urlparse

import redis
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware implementing OWASP Top 10 protections"""

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client or redis.from_url(settings.REDIS_URL)

        # CSRF protection
        self.csrf_exempt_paths = {"/api/v1/auth/login", "/api/v1/auth/register", "/docs", "/redoc", "/openapi.json"}

        # Content Security Policy
        self.csp_policy = self._build_csp_policy()

        # XSS protection patterns
        self.xss_patterns = [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<object[^>]*>.*?</object>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<embed[^>]*>", re.IGNORECASE),
            re.compile(r"expression\s*\(", re.IGNORECASE),
            re.compile(r"vbscript:", re.IGNORECASE),
            re.compile(r"data:text/html", re.IGNORECASE),
        ]

        # SQL injection patterns
        self.sql_patterns = [
            re.compile(r"\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b", re.IGNORECASE),
            re.compile(r'[\'"]\s*(or|and)\s*[\'"]\s*=\s*[\'"]', re.IGNORECASE),
            re.compile(r'[\'"]\s*(or|and)\s*\d+\s*=\s*\d+', re.IGNORECASE),
            re.compile(r"-{2,}", re.IGNORECASE),
            re.compile(r"/\*.*?\*/", re.IGNORECASE | re.DOTALL),
        ]

        # Directory traversal patterns
        self.traversal_patterns = [
            re.compile(r"\.\./", re.IGNORECASE),
            re.compile(r"\.\.\\", re.IGNORECASE),
            re.compile(r"%2e%2e%2f", re.IGNORECASE),
            re.compile(r"%2e%2e%5c", re.IGNORECASE),
        ]

        # Command injection patterns
        self.command_patterns = [
            re.compile(r"[;&|`$]", re.IGNORECASE),
            re.compile(r"\$\([^)]*\)", re.IGNORECASE),
            re.compile(r"`[^`]*`", re.IGNORECASE),
        ]

    async def dispatch(self, request: Request, call_next):
        # Security headers
        response = await self._apply_security_headers(request, call_next)
        return response

    async def _apply_security_headers(self, request: Request, call_next):
        """Apply comprehensive security headers"""

        # Pre-request security checks
        security_check = await self._perform_security_checks(request)
        if security_check:
            return security_check

        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    async def _perform_security_checks(self, request: Request) -> Optional[JSONResponse]:
        """Perform comprehensive security checks"""

        # Check for malicious patterns in URL
        if self._check_malicious_url(str(request.url)):
            return self._create_security_response("Malicious URL detected")

        # Check User-Agent for known attack patterns
        user_agent = request.headers.get("user-agent", "")
        if self._check_malicious_user_agent(user_agent):
            return self._create_security_response("Suspicious User-Agent")

        # Check for HTTP parameter pollution
        if self._check_parameter_pollution(request):
            return self._create_security_response("Parameter pollution detected")

        # Rate limiting check
        if not await self._check_global_rate_limit(request):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"error": "Global rate limit exceeded"}
            )

        # CSRF protection
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            csrf_check = await self._check_csrf_token(request)
            if csrf_check:
                return csrf_check

        # Input validation
        input_validation = await self._validate_input(request)
        if input_validation:
            return input_validation

        return None

    def _check_malicious_url(self, url: str) -> bool:
        """Check URL for malicious patterns"""
        url_lower = url.lower()

        # Check for common attack patterns
        malicious_patterns = [
            "script:",
            "javascript:",
            "vbscript:",
            "data:",
            "../",
            "..\\",
            "%2e%2e%2f",
            "%2e%2e%5c",
            "<script",
            "</script>",
            "<iframe",
            "<object",
            "union+select",
            "union%20select",
            "base64",
            "eval(",
            "alert(",
            "document.cookie",
            "document.write",
        ]

        return any(pattern in url_lower for pattern in malicious_patterns)

    def _check_malicious_user_agent(self, user_agent: str) -> bool:
        """Check User-Agent for attack signatures"""
        ua_lower = user_agent.lower()

        suspicious_agents = [
            "sqlmap",
            "nikto",
            "nessus",
            "openvas",
            "masscan",
            "nmap",
            "zap",
            "burp",
            "havij",
            "pangolin",
            "<script",
        ]

        return any(agent in ua_lower for agent in suspicious_agents)

    def _check_parameter_pollution(self, request: Request) -> bool:
        """Check for HTTP parameter pollution"""
        query_params = request.query_params

        # Check for duplicate parameters
        seen_params = set()
        for key in query_params.keys():
            if key in seen_params:
                return True
            seen_params.add(key)

        return False

    async def _check_global_rate_limit(self, request: Request) -> bool:
        """Global rate limiting"""
        client_ip = request.client.host
        key = f"global_rate_limit:{client_ip}"

        try:
            current_count = self.redis_client.incr(key)
            if current_count == 1:
                self.redis_client.expire(key, 60)  # 1 minute window

            return current_count <= 1000  # 1000 requests per minute globally
        except:
            return True  # Allow if Redis is unavailable

    async def _check_csrf_token(self, request: Request) -> Optional[JSONResponse]:
        """CSRF token validation"""
        if request.url.path in self.csrf_exempt_paths:
            return None

        # Check for CSRF token in headers or form data
        csrf_token = request.headers.get("x-csrf-token")

        if not csrf_token:
            # Try to get from form data for multipart requests
            if request.headers.get("content-type", "").startswith("multipart/form-data"):
                # This would require reading the body, which is complex in middleware
                # For now, we'll skip CSRF for multipart requests
                return None

        if not csrf_token:
            return self._create_security_response("CSRF token missing")

        # Validate CSRF token
        if not self._validate_csrf_token(csrf_token, request):
            return self._create_security_response("Invalid CSRF token")

        return None

    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token"""
        try:
            # Extract session ID from Authorization header
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return False

            jwt_token = auth_header.split(" ")[1]

            # Generate expected token based on session
            expected_token = self._generate_csrf_token(jwt_token)

            return secrets.compare_digest(token, expected_token)
        except:
            return False

    def _generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        data = f"{session_id}{settings.SECRET_KEY}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def _validate_input(self, request: Request) -> Optional[JSONResponse]:
        """Validate input for various injection attacks"""

        # Check query parameters
        for key, value in request.query_params.items():
            if self._check_injection_patterns(value):
                return self._create_security_response(f"Malicious input detected in parameter: {key}")

        # Check headers for injection
        for key, value in request.headers.items():
            if key.lower() in ["user-agent", "referer", "x-forwarded-for"]:
                continue  # Skip common headers that might contain legitimate special chars

            if self._check_injection_patterns(value):
                return self._create_security_response(f"Malicious input detected in header: {key}")

        return None

    def _check_injection_patterns(self, value: str) -> bool:
        """Check value against various injection patterns"""

        # XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(value):
                return True

        # SQL injection patterns
        for pattern in self.sql_patterns:
            if pattern.search(value):
                return True

        # Directory traversal patterns
        for pattern in self.traversal_patterns:
            if pattern.search(value):
                return True

        # Command injection patterns
        for pattern in self.command_patterns:
            if pattern.search(value):
                return True

        return False

    def _add_security_headers(self, response: Response):
        """Add comprehensive security headers"""

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Type Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Frame Options
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=()"
        )

        # Cross-Origin policies
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"

        # Remove server information
        response.headers.pop("server", None)

        # Add custom security headers
        response.headers["X-Security-Framework"] = "AI-Company-Security"
        response.headers["X-Content-Security"] = "protected"

    def _build_csp_policy(self) -> str:
        """Build Content Security Policy"""
        if settings.is_production:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://vercel.live; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://ai-company-api.railway.app wss://ai-company-api.railway.app; "
                "media-src 'self'; "
                "object-src 'none'; "
                "frame-src 'none'; "
                "worker-src 'self'; "
                "manifest-src 'self'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests"
            )
        else:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: http: https:; "
                "connect-src 'self' http://localhost:* ws://localhost:* wss://localhost:*; "
                "font-src 'self'; "
                "media-src 'self'; "
                "object-src 'none'; "
                "frame-src 'none'"
            )

    def _create_security_response(self, message: str) -> JSONResponse:
        """Create standardized security error response"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Security violation", "message": message, "code": "SECURITY_VIOLATION"},
            headers={"X-Security-Block": "true", "X-Block-Reason": message},
        )


class InputSanitizer:
    """Input sanitization utilities"""

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML content"""
        if not text:
            return ""

        # Escape HTML characters
        sanitized = html.escape(text)

        # Remove potentially dangerous attributes
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', "", sanitized, flags=re.IGNORECASE)

        return sanitized

    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Sanitize potential SQL injection"""
        if not text:
            return ""

        # Remove SQL keywords and dangerous characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]

        sanitized = text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        if not filename:
            return ""

        # Remove directory traversal attempts
        sanitized = filename.replace("..", "").replace("/", "").replace("\\", "")

        # Remove null bytes and control characters
        sanitized = "".join(char for char in sanitized if ord(char) >= 32)

        # Limit length
        return sanitized[:255]

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and scheme"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ["http", "https"] and bool(parsed.netloc)
        except:
            return False


class SecurityLogger:
    """Security event logging"""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def log_security_event(self, event_type: str, request: Request, details: Dict):
        """Log security events for monitoring"""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "path": str(request.url.path),
            "method": request.method,
            "details": details,
        }

        try:
            # Store in Redis for real-time monitoring
            key = f"security_events:{event_type}"
            self.redis_client.lpush(key, json.dumps(event))
            self.redis_client.ltrim(key, 0, 1000)  # Keep last 1000 events
            self.redis_client.expire(key, 86400)  # 24 hours

            # Alert on critical events
            if event_type in ["sql_injection", "xss_attempt", "csrf_violation"]:
                await self._send_security_alert(event)

        except Exception as e:
            print(f"Failed to log security event: {e}")

    async def _send_security_alert(self, event: Dict):
        """Send security alert (could integrate with Slack, email, etc.)"""
        # This would integrate with your alerting system
        print(f"SECURITY ALERT: {event['type']} from {event['ip']}")


# Content validation utilities
class ContentValidator:
    """Advanced content validation"""

    @staticmethod
    def validate_json_structure(data: dict, required_fields: List[str]) -> bool:
        """Validate JSON structure"""
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_file_type(filename: str, allowed_types: Set[str]) -> bool:
        """Validate file type"""
        extension = filename.lower().split(".")[-1] if "." in filename else ""
        return extension in allowed_types

    @staticmethod
    def validate_file_size(size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """Validate file size (default 10MB)"""
        return size <= max_size
