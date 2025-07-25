#!/usr/bin/env python3
"""
GitHub Integration Security Configuration
Iron Will 95% Compliance - Comprehensive Security Implementation
"""

import hashlib
import logging
import os
import secrets
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class GitHubSecurityConfig:
    """
    🔒 Iron Will Compliant Security Configuration

    Features:
    - Token management
    - SSL/TLS configuration
    - Input validation
    - Rate limiting
    - Audit logging
    """

    def __init__(self):
        """Initialize security configuration"""
        self.token_file = os.path.expanduser("~/.github_token")
        self.ssl_context = self._create_ssl_context()
        self.rate_limits = {
            "api_calls": {"limit": 5000, "window": 3600},

        }

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create secure SSL context"""
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return context

    def get_token(self) -> str:
        """Get GitHub token securely"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as f:
                    token = f.read().strip()
                    if len(token) >= 10:
                        return token

            # Fallback to environment variable
            token = os.environ.get("GITHUB_TOKEN")
            if token and len(token) >= 10:
                return token

            raise SecurityError("Valid GitHub token not found")

        except Exception as e:
            logger.error(f"Token retrieval failed: {str(e)}")
            raise SecurityError(f"Token retrieval failed: {str(e)}")

    def validate_input(self, data: Any, field_name: str) -> bool:
        """Validate input data for security"""
        try:
            if isinstance(data, str):
                # Check for SQL injection patterns
                sql_patterns = [
                    "'",
                    '"',
                    ";",
                    "--",
                    "/*",
                    "*/",
                    "DROP",
                    "DELETE",
                    "UPDATE",
                ]
                for pattern in sql_patterns:
                    if pattern.lower() in data.lower():
                        raise SecurityError(
                            f"Suspicious pattern detected in {field_name}"
                        )

                # Check for XSS patterns
                xss_patterns = [
                    "<script>",
                    "</script>",
                    "javascript:",
                    "onclick=",
                    "onerror=",
                ]
                for pattern in xss_patterns:
                    if pattern.lower() in data.lower():
                        raise SecurityError(f"XSS pattern detected in {field_name}")

                # Length validation
                if len(data) > 10000:
                    raise SecurityError(f"Input too long for {field_name}")

            return True

        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Input validation failed: {str(e)}")
            raise SecurityError(f"Input validation failed: {str(e)}")

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:8]

    def generate_request_id(self) -> str:
        """Generate unique request ID for tracking"""
        return secrets.token_hex(16)

class SecurityError(Exception):
    """Security-related error"""

    pass
