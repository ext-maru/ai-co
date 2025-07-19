#!/usr/bin/env python3
"""
GitHub Integration Comprehensive Security System
Iron Will 95% Compliance - Full Security Implementation
"""

import os
import re
import ssl
import jwt
import json
import hmac
import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class SecurityViolationError(Exception):
    """Security violation detected"""
    pass

class AuthenticationError(Exception):
    """Authentication failed"""
    pass

class AuthorizationError(Exception):
    """Authorization failed"""
    pass

class EncryptionError(Exception):
    """Encryption/Decryption failed"""
    pass

class GitHubSecurityManager:
    """
    🔒 Iron Will Compliant Security Manager
    
    Features:
    - Token encryption and secure storage
    - Request signature verification
    - Input sanitization
    - SQL/XSS injection prevention
    - Rate limiting
    - Audit logging
    - HTTPS enforcement
    - Secret scanning
    """
    
    def __init__(self):
        """Initialize security manager"""
        try:
            self.encryption_key = self._get_or_create_encryption_key()
            self.fernet = Fernet(self.encryption_key)
            self.jwt_secret = self._get_or_create_jwt_secret()
            
            # Security patterns
            self.sql_injection_patterns = [
                r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
                r"(--|#|/\*|\*/)",
                r"(\bOR\b\s*\d+\s*=\s*\d+)",
                r"(\bAND\b\s*\d+\s*=\s*\d+)",
                r"('(\s|%20)*(OR|AND)(\s|%20)*')",
            ]
            
            self.xss_patterns = [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
                r"<link[^>]*>",
                r"eval\s*\(",
                r"expression\s*\(",
            ]
            
            self.path_traversal_patterns = [
                r"\.\./",
                r"\.\.\\/",
                r"%2e%2e/",
                r"%252e%252e/",
                r"\.\.%2f",
                r"\.\.%5c",
            ]
            
            # Initialize audit log
            self.audit_log_path = Path("logs/security_audit")
            self.audit_log_path.mkdir(parents=True, exist_ok=True)
            
            # Rate limiting storage
            self.rate_limits = {}
            self.failed_auth_attempts = {}
            
            logger.info("🔒 GitHub Security Manager initialized")
            
        except Exception as e:
            logger.error(f"Security manager initialization failed: {str(e)}")
            raise
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = Path.home() / ".github_security" / "encryption.key"
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Secure file permissions
            return key
    
    def _get_or_create_jwt_secret(self) -> str:
        """Get or create JWT secret"""
        secret_file = Path.home() / ".github_security" / "jwt.secret"
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        
        if secret_file.exists():
            return secret_file.read_text().strip()
        else:
            secret = secrets.token_hex(32)
            secret_file.write_text(secret)
            secret_file.chmod(0o600)  # Secure file permissions
            return secret
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt GitHub token"""
        try:
            if not token:
                raise ValueError("Token cannot be empty")
            
            encrypted = self.fernet.encrypt(token.encode())
            return encrypted.decode()
            
        except Exception as e:
            logger.error(f"Token encryption failed: {str(e)}")
            raise EncryptionError(f"Token encryption failed: {str(e)}")
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt GitHub token"""
        try:
            if not encrypted_token:
                raise ValueError("Encrypted token cannot be empty")
            
            decrypted = self.fernet.decrypt(encrypted_token.encode())
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Token decryption failed: {str(e)}")
            raise EncryptionError(f"Token decryption failed: {str(e)}")
    
    def validate_and_sanitize_input(self, input_data: Any, field_name: str) -> Any:
        """Validate and sanitize input data"""
        try:
            if input_data is None:
                return None
            
            if isinstance(input_data, str):
                # Check for SQL injection
                for pattern in self.sql_injection_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        self._log_security_event("sql_injection_attempt", {
                            "field": field_name,
                            "pattern": pattern,
                            "input_preview": input_data[:50]
                        })
                        raise SecurityViolationError(f"SQL injection pattern detected in {field_name}")
                
                # Check for XSS
                for pattern in self.xss_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        self._log_security_event("xss_attempt", {
                            "field": field_name,
                            "pattern": pattern,
                            "input_preview": input_data[:50]
                        })
                        raise SecurityViolationError(f"XSS pattern detected in {field_name}")
                
                # Check for path traversal
                for pattern in self.path_traversal_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        self._log_security_event("path_traversal_attempt", {
                            "field": field_name,
                            "pattern": pattern,
                            "input_preview": input_data[:50]
                        })
                        raise SecurityViolationError(f"Path traversal pattern detected in {field_name}")
                
                # Sanitize string
                # Remove null bytes
                sanitized = input_data.replace('\x00', '')
                
                # Remove control characters except tab, newline, carriage return
                sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)
                
                # Limit length based on field type
                max_lengths = {
                    "repo_name": 100,
                    "username": 39,
                    "branch_name": 250,
                    "title": 200,
                    "description": 500,
                    "body": 50000,
                    "path": 500,
                    "url": 2000
                }
                
                max_length = max_lengths.get(field_name, 10000)
                if len(sanitized) > max_length:
                    sanitized = sanitized[:max_length]
                
                return sanitized
                
            elif isinstance(input_data, dict):
                # Recursively sanitize dictionary
                return {k: self.validate_and_sanitize_input(v, f"{field_name}.{k}") for k, v in input_data.items()}
            
            elif isinstance(input_data, list):
                # Recursively sanitize list
                return [self.validate_and_sanitize_input(item, f"{field_name}[{i}]") for i, item in enumerate(input_data)]
            
            else:
                # For other types, return as is
                return input_data
                
        except SecurityViolationError:
            raise
        except Exception as e:
            logger.error(f"Input validation failed for {field_name}: {str(e)}")
            raise SecurityViolationError(f"Input validation failed: {str(e)}")
    
    def generate_request_signature(self, method: str, url: str, body: Optional[str] = None) -> str:
        """Generate HMAC signature for request"""
        try:
            timestamp = str(int(datetime.now().timestamp()))
            
            # Create signature payload
            payload_parts = [method.upper(), url, timestamp]
            if body:
                payload_parts.append(body)
            
            payload = '\n'.join(payload_parts)
            
            # Generate HMAC
            signature = hmac.new(
                self.jwt_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return f"{timestamp}.{signature}"
            
        except Exception as e:
            logger.error(f"Signature generation failed: {str(e)}")
            raise SecurityViolationError(f"Signature generation failed: {str(e)}")
    
    def verify_request_signature(self, signature: str, method: str, url: str, body: Optional[str] = None) -> bool:
        """Verify request signature"""
        try:
            parts = signature.split('.')
            if len(parts) != 2:
                return False
            
            timestamp, provided_signature = parts
            
            # Check timestamp (5 minute window)
            request_time = int(timestamp)
            current_time = int(datetime.now().timestamp())
            if abs(current_time - request_time) > 300:
                return False
            
            # Recreate signature
            expected_signature = self.generate_request_signature(method, url, body).split('.')[1]
            
            # Constant time comparison
            return hmac.compare_digest(expected_signature, provided_signature)
            
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False
    
    def check_rate_limit(self, identifier: str, limit: int = 100, window: int = 3600) -> bool:
        """Check rate limit"""
        try:
            current_time = datetime.now()
            window_start = current_time - timedelta(seconds=window)
            
            if identifier not in self.rate_limits:
                self.rate_limits[identifier] = []
            
            # Remove old entries
            self.rate_limits[identifier] = [
                timestamp for timestamp in self.rate_limits[identifier]
                if timestamp > window_start
            ]
            
            # Check limit
            if len(self.rate_limits[identifier]) >= limit:
                self._log_security_event("rate_limit_exceeded", {
                    "identifier": identifier,
                    "limit": limit,
                    "window": window,
                    "current_count": len(self.rate_limits[identifier])
                })
                return False
            
            # Add current request
            self.rate_limits[identifier].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return False
    
    def record_failed_auth(self, identifier: str) -> None:
        """Record failed authentication attempt"""
        try:
            if identifier not in self.failed_auth_attempts:
                self.failed_auth_attempts[identifier] = []
            
            self.failed_auth_attempts[identifier].append(datetime.now())
            
            # Check for brute force
            recent_attempts = [
                attempt for attempt in self.failed_auth_attempts[identifier]
                if attempt > datetime.now() - timedelta(minutes=15)
            ]
            
            if len(recent_attempts) >= 5:
                self._log_security_event("brute_force_detected", {
                    "identifier": identifier,
                    "attempts": len(recent_attempts)
                })
                
        except Exception as e:
            logger.error(f"Failed auth recording error: {str(e)}")
    
    def create_secure_ssl_context(self) -> ssl.SSLContext:
        """Create secure SSL context"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            # Disable weak ciphers
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            return context
            
        except Exception as e:
            logger.error(f"SSL context creation failed: {str(e)}")
            raise SecurityViolationError(f"SSL context creation failed: {str(e)}")
    
    def scan_for_secrets(self, content: str) -> List[Dict[str, Any]]:
        """Scan content for potential secrets"""
        try:
            secrets_found = []
            
            # Common secret patterns
            secret_patterns = {
                "github_token": r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59})",
                "aws_access_key": r"(AKIA[0-9A-Z]{16})",
                "aws_secret_key": r"([a-zA-Z0-9+/]{40})",
                "api_key": r"(api[_-]?key[_-]?[:=]\s*['\"]?[a-zA-Z0-9]{32,}['\"]?)",
                "private_key": r"(-----BEGIN (RSA |EC )?PRIVATE KEY-----)",
                "jwt": r"(eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)"
            }
            
            for secret_type, pattern in secret_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    secrets_found.append({
                        "type": secret_type,
                        "location": match.start(),
                        "preview": match.group()[:20] + "..." if len(match.group()) > 20 else match.group()
                    })
            
            if secrets_found:
                self._log_security_event("secrets_detected", {
                    "count": len(secrets_found),
                    "types": list(set(s["type"] for s in secrets_found))
                })
            
            return secrets_found
            
        except Exception as e:
            logger.error(f"Secret scanning failed: {str(e)}")
            return []
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security event"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details
            }
            
            # Write to audit log
            log_file = self.audit_log_path / f"audit_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
            
            # Also log to standard logger
            logger.warning(f"Security event: {event_type} - {details}")
            
        except Exception as e:
            logger.error(f"Security event logging failed: {str(e)}")
    
    def secure_decorator(self, require_auth: bool = True, rate_limit: int = 100):
        """Decorator for securing functions"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    # Extract context (assuming first arg is self with token attribute)
                    if args and hasattr(args[0], 'token'):
                        token = args[0].token
                        identifier = hashlib.sha256(token.encode()).hexdigest()[:16]
                        
                        # Check rate limit
                        if not self.check_rate_limit(identifier, rate_limit):
                            raise SecurityViolationError("Rate limit exceeded")
                        
                        # Validate token if required
                        if require_auth and not token:
                            raise AuthenticationError("Authentication required")
                    
                    # Sanitize all string arguments
                    sanitized_kwargs = {}
                    for key, value in kwargs.items():
                        if isinstance(value, str):
                            sanitized_kwargs[key] = self.validate_and_sanitize_input(value, key)
                        else:
                            sanitized_kwargs[key] = value
                    
                    # Execute function
                    result = await func(*args, **sanitized_kwargs)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Security decorator error in {func.__name__}: {str(e)}")
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    # Similar logic for sync functions
                    if args and hasattr(args[0], 'token'):
                        token = args[0].token
                        identifier = hashlib.sha256(token.encode()).hexdigest()[:16]
                        
                        if not self.check_rate_limit(identifier, rate_limit):
                            raise SecurityViolationError("Rate limit exceeded")
                        
                        if require_auth and not token:
                            raise AuthenticationError("Authentication required")
                    
                    # Sanitize kwargs
                    sanitized_kwargs = {}
                    for key, value in kwargs.items():
                        if isinstance(value, str):
                            sanitized_kwargs[key] = self.validate_and_sanitize_input(value, key)
                        else:
                            sanitized_kwargs[key] = value
                    
                    return func(*args, **sanitized_kwargs)
                    
                except Exception as e:
                    logger.error(f"Security decorator error in {func.__name__}: {str(e)}")
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP requests"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "no-referrer-when-downgrade"
        }

# Global security manager instance
_security_manager = None

def get_security_manager() -> GitHubSecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = GitHubSecurityManager()
    return _security_manager

# Export
__all__ = [
    'GitHubSecurityManager',
    'get_security_manager',
    'SecurityViolationError',
    'AuthenticationError',
    'AuthorizationError',
    'EncryptionError'
]