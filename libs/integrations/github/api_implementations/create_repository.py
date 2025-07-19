#!/usr/bin/env python3
"""
GitHub Repository Creation API Implementation
Iron Will 95% Compliance - Error Handling & Security Enhanced
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import ssl

logger = logging.getLogger(__name__)

class GitHubRepositoryCreator:
    """
    🗡️ Iron Will Compliant GitHub Repository Creator
    
    Features:
    - Comprehensive error handling
    - Security validation
    - Authentication management
    - Rate limiting
    - Audit logging
    """
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """
        Initialize repository creator with security validation
        
        Args:
            token: GitHub authentication token
            base_url: GitHub API base URL
            
        Raises:
            ValueError: If token is invalid
            SecurityError: If URL is not HTTPS
        """
        try:
            if not token or len(token) < 10:
                raise ValueError("GitHub token must be at least 10 characters")
            
            if not base_url.startswith("https://"):
                raise SecurityError("Only HTTPS URLs are allowed")
            
            self.token = token
            self.base_url = base_url
            self.session = None
            
            # Audit logging
            logger.info(f"GitHubRepositoryCreator initialized at {datetime.now()}")
            
        except Exception as e:
            logger.error(f"GitHubRepositoryCreator initialization failed: {str(e)}")
            raise
    
    async def create_repository(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create GitHub repository with comprehensive validation
        
        Args:
            repo_data: Repository configuration data
            
        Returns:
            Dict containing repository information
            
        Raises:
            ValidationError: If input data is invalid
            AuthenticationError: If authentication fails
            APIError: If GitHub API call fails
        """
        try:
            # Input validation
            if not isinstance(repo_data, dict):
                raise ValidationError("Repository data must be a dictionary")
            
            if not repo_data.get("name"):
                raise ValidationError("Repository name is required")
            
            # Sanitize input
            sanitized_data = self._sanitize_repository_data(repo_data)
            
            # Create session if needed
            if not self.session:
                await self._create_session()
            
            # API call with error handling
            response = await self._make_api_call(
                method="POST",
                endpoint="/user/repos",
                data=sanitized_data
            )
            
            # Audit logging
            logger.info(f"Repository created successfully: {sanitized_data['name']}")
            
            return {
                "success": True,
                "repository": response,
                "created_at": datetime.now().isoformat()
            }
            
        except ValidationError as e:
            logger.error(f"Repository creation validation failed: {str(e)}")
            raise
        except AuthenticationError as e:
            logger.error(f"Repository creation authentication failed: {str(e)}")
            raise
        except APIError as e:
            logger.error(f"Repository creation API failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Repository creation unexpected error: {str(e)}")
            raise APIError(f"Unexpected error during repository creation: {str(e)}")
    
    def _sanitize_repository_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize repository data for security
        
        Args:
            data: Raw repository data
            
        Returns:
            Sanitized repository data
        """
        try:
            sanitized = {}
            
            # Required fields
            sanitized["name"] = str(data["name"]).strip()[:100]  # Limit length
            
            # Optional fields with validation
            if "description" in data:
                sanitized["description"] = str(data["description"]).strip()[:500]
            
            if "private" in data:
                sanitized["private"] = bool(data["private"])
            
            if "auto_init" in data:
                sanitized["auto_init"] = bool(data["auto_init"])
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Data sanitization failed: {str(e)}")
            raise ValidationError(f"Data sanitization failed: {str(e)}")
    
    async def _create_session(self):
        """Create secure HTTP session"""
        try:
            # SSL context for security
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            # HTTP connector with security settings
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            
            # Session with authentication headers
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHubIntegration/1.0"
            }
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
        except Exception as e:
            logger.error(f"Session creation failed: {str(e)}")
            raise AuthenticationError(f"Session creation failed: {str(e)}")
    
    async def _make_api_call(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make authenticated API call with error handling
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            
        Returns:
            API response data
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            async with self.session.request(
                method=method,
                url=url,
                json=data
            ) as response:
                
                # Rate limiting check
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_api_call(method, endpoint, data)
                
                # Authentication check
                if response.status == 401:
                    raise AuthenticationError("Invalid GitHub token")
                
                # API error check
                if response.status >= 400:
                    error_data = await response.json()
                    raise APIError(f"API call failed: {error_data.get('message', 'Unknown error')}")
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {str(e)}")
            raise APIError(f"HTTP client error: {str(e)}")
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            raise APIError(f"API call failed: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

# Custom exceptions for better error handling
class ValidationError(Exception):
    """Input validation error"""
    pass

class AuthenticationError(Exception):
    """Authentication error"""
    pass

class APIError(Exception):
    """API call error"""
    pass

class SecurityError(Exception):
    """Security violation error"""
    pass

# Usage example
async def main():
    """Example usage"""
    try:
        async with GitHubRepositoryCreator("github_token_here") as creator:
            result = await creator.create_repository({
                "name": "test-repo",
                "description": "Test repository",
                "private": True,
                "auto_init": True
            })
            print(f"Repository created: {result}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
