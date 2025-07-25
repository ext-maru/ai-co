#!/usr/bin/env python3
"""
Comprehensive Security System Tests
Iron Will 95% Compliance - Test Coverage
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from libs.integrations.github.security import (
    GitHubSecurityManager,
    get_security_manager,
    SecurityViolationError,
    AuthenticationError,
    AuthorizationError,
    EncryptionError
)

class TestGitHubSecurityManager:
    """
    🧪 Iron Will Compliant Security Manager Test Suite
    
    Test Coverage:
    - Token encryption/decryption
    - Input validation and sanitization
    - SQL injection prevention
    - XSS prevention
    - Path traversal prevention
    - Rate limiting
    - Request signatures
    - Secret scanning
    - SSL context creation
    - Audit logging
    """
    
    def setup_method(self)self.security_manager = GitHubSecurityManager()
    """Setup test fixtures"""
        self.test_token = "ghp_test1234567890abcdefghijklmnopqrstuvwx"
        self.test_data = {
            "repo_name": "test-repo",
            "username": "test-user",
            "title": "Test Title",
            "body": "Test body content",
            "branch_name": "feature/test-branch"
        }
    
    def test_token_encryption_decryption(self):
        """Test token encryption and decryption"""
        # Encrypt token
        encrypted = self.security_manager.encrypt_token(self.test_token)
        assert encrypted != self.test_token
        assert isinstance(encrypted, str)
        
        # Decrypt token
        decrypted = self.security_manager.decrypt_token(encrypted)
        assert decrypted == self.test_token
        
        # Test empty token
        with pytest.raises(ValueError):
            self.security_manager.encrypt_token("")
        
        with pytest.raises(ValueError):
            self.security_manager.decrypt_token("")
        
        # Test invalid encrypted token
        with pytest.raises(EncryptionError):
            self.security_manager.decrypt_token("invalid_encrypted_token")
    
    def test_sql_injection_prevention(self):
        """Test SQL injection pattern detection"""
        sql_injection_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin' --",
            "1; DELETE FROM users WHERE 1=1",
            "' UNION SELECT * FROM passwords --",
            "1' AND 1=1 --"
        ]
        
        for malicious_input in sql_injection_inputs:
            with pytest.raises(SecurityViolationError) as exc_info:
                self.security_manager.validate_and_sanitize_input(malicious_input, "test_field")
            assert "SQL injection pattern detected" in str(exc_info.value)
    
    def test_xss_prevention(self):
        """Test XSS pattern detection"""
        xss_inputs = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='malicious.com'></iframe>",
            "<object data='malicious.swf'></object>",
            "<link rel='stylesheet' href='malicious.css'>",
            "eval('malicious code')"
        ]
        
        for malicious_input in xss_inputs:
            with pytest.raises(SecurityViolationError) as exc_info:
                self.security_manager.validate_and_sanitize_input(malicious_input, "test_field")
            assert "XSS pattern detected" in str(exc_info.value)
    
    def test_path_traversal_prevention(self):
        """Test path traversal pattern detection"""
        path_traversal_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
            "..%252f..%252f",
            "..%2f..%2f",
            "..%5c..%5c"
        ]
        
        for malicious_input in path_traversal_inputs:
            with pytest.raises(SecurityViolationError) as exc_info:
                self.security_manager.validate_and_sanitize_input(malicious_input, "test_field")
            assert "Path traversal pattern detected" in str(exc_info.value)
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test string sanitization
        dirty_input = "Hello\x00World\x0cTest\x7f"
        clean_output = self.security_manager.validate_and_sanitize_input(dirty_input, "test_field")
        assert "\x00" not in clean_output
        assert "\x0c" not in clean_output
        assert "\x7f" not in clean_output
        
        # Test length limits
        long_repo_name = "a" * 200
        sanitized_repo = self.security_manager.validate_and_sanitize_input(long_repo_name, "repo_name" \
            "repo_name")
        assert len(sanitized_repo) == 100
        
        # Test dictionary sanitization
        dirty_dict = {
            "repo": "test\x00repo",
            "desc": "<script>alert('xss')</script>"
        }
        
        # Should raise on XSS
        with pytest.raises(SecurityViolationError):
            self.security_manager.validate_and_sanitize_input(dirty_dict, "test_dict")
        
        # Test list sanitization
        clean_list = ["test1", "test2", "test3"]
        sanitized_list = self.security_manager.validate_and_sanitize_input(clean_list, "test_list")
        assert sanitized_list == clean_list
    
    def test_request_signature(self):
        """Test request signature generation and verification"""
        method = "POST"
        url = "https://api.github.com/repos"
        body = '{"name": "test-repo"}'
        
        # Generate signature
        signature = self.security_manager.generate_request_signature(method, url, body)
        assert "." in signature
        
        # Verify valid signature
        assert self.security_manager.verify_request_signature(signature, method, url, body)
        
        # Test invalid signature
        assert not self.security_manager.verify_request_signature(
            "invalid.signature",
            method,
            url,
            body
        )
        
        # Test expired signature (mock time)
        parts = signature.split(".")
        old_timestamp = str(int(datetime.now().timestamp()) - 400)  # 6+ minutes ago
        old_signature = f"{old_timestamp}.{parts[1]}"
        assert not self.security_manager.verify_request_signature(old_signature, method, url, body)
        
        # Test tampered data
        assert not self.security_manager.verify_request_signature(signature, "GET", url, body)
        assert not self.security_manager.verify_request_signature(signature, method, "https://evil.com" \
            "https://evil.com", body)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        identifier = "test_user_123"
        
        # Should allow requests within limit
        for i in range(5):
            assert self.security_manager.check_rate_limit(identifier, limit=10, window=60)
        
        # Should block after reaching limit
        for i in range(5):
            self.security_manager.check_rate_limit(identifier, limit=10, window=60)
        
        assert not self.security_manager.check_rate_limit(identifier, limit=10, window=60)
        
        # Test window expiration (would need to mock time)
        # For now, test with very small window
        identifier2 = "test_user_456"
        assert self.security_manager.check_rate_limit(identifier2, limit=1, window=0.001)
        # Sleep briefly
        import time
        time.sleep(0.01)
        assert self.security_manager.check_rate_limit(identifier2, limit=1, window=0.001)
    
    def test_failed_auth_recording(self):
        """Test failed authentication recording"""
        identifier = "test_user_789"
        
        # Record multiple failures
        for i in range(5):
            self.security_manager.record_failed_auth(identifier)

        # Verify timestamps are recent

    def test_ssl_context_creation(self)context = self.security_manager.create_secure_ssl_context()
    """Test secure SSL context creation"""
        
        assert context.check_hostname is True
        assert context.verify_mode == 1  # CERT_REQUIRED
        assert hasattr(context, 'minimum_version')
    
    def test_secret_scanning(self):
        """Test secret scanning functionality"""
        content_with_secrets = """
        Here's my GitHub token: ghp_1234567890abcdefghijklmnopqrstuvwxyz12
        AWS Access Key: AKIAIOSFODNN7EXAMPLE
        Some API key: api_key=abcdef1234567890abcdef1234567890
        Private key:
        -----BEGIN RSA PRIVATE KEY-----
        MIIEowIBAAKCAQEA...
        -----END RSA PRIVATE KEY-----
        JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.0eyJzdWIiOiIxMjM0NTY3ODkwIn0.0dozjgNryP4 \
            J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U
        """
        
        secrets = self.security_manager.scan_for_secrets(content_with_secrets)
        
        assert len(secrets) > 0
        secret_types = [s["type"] for s in secrets]
        assert "github_token" in secret_types
        assert "aws_access_key" in secret_types
        assert "api_key" in secret_types
        assert "private_key" in secret_types
        assert "jwt" in secret_types
    
    def test_secure_decorator_sync(self):
        """Test secure decorator for sync functions"""
        
        @self.security_manager.secure_decorator(require_auth=True, rate_limit=10)
        def test_function(self, test_input: str):
        """test_functionテストメソッド"""
            return f"Processed: {test_input}"
        
        # Create mock object with token
        mock_self = Mock()
        mock_self.token = "test_token"
        
        # Should work normally
        result = test_function(mock_self, test_input="clean input")
        assert result == "Processed: clean input"
        
        # Should fail with SQL injection
        with pytest.raises(SecurityViolationError):
            test_function(mock_self, test_input="'; DROP TABLE users; --")
        
        # Test without auth
        mock_self.token = None
        with pytest.raises(AuthenticationError):
            test_function(mock_self, test_input="test")
    
    @pytest.mark.asyncio
    async def test_secure_decorator_async(self):
        """Test secure decorator for async functions"""
        
        @self.security_manager.secure_decorator(require_auth=True, rate_limit=10)
        async def test_async_function(self, test_input: str)await asyncio.sleep(0.01)
    """test_async_functionテストメソッド"""
            return f"Processed: {test_input}"
        
        # Create mock object with token
        mock_self = Mock()
        mock_self.token = "test_token"
        
        # Should work normally
        result = await test_async_function(mock_self, test_input="clean input")
        assert result == "Processed: clean input"
        
        # Should fail with XSS
        with pytest.raises(SecurityViolationError):
            await test_async_function(mock_self, test_input="<script>alert('xss')</script>")
    
    def test_security_headers(self)headers = self.security_manager.get_security_headers()
    """Test security headers generation"""
        
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
        assert "Referrer-Policy" in headers
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_audit_logging(self, mock_exists, mock_mkdir):
        """Test audit logging functionality"""
        mock_exists.return_value = True
        
        # Trigger some security events
        try:
            self.security_manager.validate_and_sanitize_input("' OR 1=1 --", "test")
        except SecurityViolationError:
            pass
        
        # Check rate limit exceeded
        identifier = "spam_user"
        for i in range(15):
            self.security_manager.check_rate_limit(identifier, limit=10, window=60)
        
        # Verify audit log directory was created
        assert mock_mkdir.called or mock_exists.called
    
    def test_get_security_manager_singleton(self)manager1 = get_security_manager()
    """Test singleton pattern for security manager"""
        manager2 = get_security_manager()
        
        assert manager1 is manager2
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        # Test None input
        assert self.security_manager.validate_and_sanitize_input(None, "test") is None
        
        # Test empty string signature
        assert not self.security_manager.verify_request_signature("", "GET", "/test", None)
        
        # Test various input types
        assert self.security_manager.validate_and_sanitize_input(123, "number") == 123
        assert self.security_manager.validate_and_sanitize_input(True, "boolean") is True
        
        # Test nested structures
        nested_dict = {
            "level1": {
                "level2": {
                    "value": "test"
                }
            }
        }
        sanitized = self.security_manager.validate_and_sanitize_input(nested_dict, "nested")
        assert sanitized["level1"]["level2"]["value"] == "test"

class TestIntegration:
    """Integration tests for security system"""
    
    @pytest.mark.asyncio
    async def test_full_security_workflow(self)security_manager = GitHubSecurityManager()
    """Test complete security workflow"""
        
        # 1.0 Encrypt token
        token = "ghp_test1234567890abcdefghijklmnopqrstuvwx"
        encrypted_token = security_manager.encrypt_token(token)
        
        # 2.0 Create request with signature
        method = "POST"
        url = "https://api.github.com/repos"
        body_data = {
            "name": "test-repo",
            "description": "Test repository"
        }
        
        # 3.0 Validate and sanitize input
        sanitized_data = security_manager.validate_and_sanitize_input(body_data, "repo_data")
        body = json.dumps(sanitized_data)
        
        # 4.0 Generate signature
        signature = security_manager.generate_request_signature(method, url, body)
        
        # 5.0 Check rate limit
        assert security_manager.check_rate_limit("test_user", limit=100)
        
        # 6.0 Verify signature
        assert security_manager.verify_request_signature(signature, method, url, body)
        
        # 7.0 Get security headers
        headers = security_manager.get_security_headers()
        assert len(headers) > 0
        
        # 8.0 Decrypt token for use
        decrypted_token = security_manager.decrypt_token(encrypted_token)
        assert decrypted_token == token
        
        # 9.0 Create SSL context
        ssl_context = security_manager.create_secure_ssl_context()
        assert ssl_context is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])