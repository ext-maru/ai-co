#!/usr/bin/env python3
"""
GitHub Repository Information API Implementation
Iron Will 95% Compliance - Error Handling & Security Enhanced
"""

import asyncio
import json
import logging
import ssl
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class GitHubRepositoryInfo:
    """
    🗡️ Iron Will Compliant GitHub Repository Information Retriever

    Features:
    - Comprehensive error handling
    - Security validation
    - Caching support
    - Rate limiting
    - Audit logging
    """

    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """Initialize repository info retriever with security validation"""
        try:
            if not token or len(token) < 10:
                raise ValueError("GitHub token must be at least 10 characters")

            if not base_url.startswith("https://"):
                raise SecurityError("Only HTTPS URLs are allowed")

            self.token = token
            self.base_url = base_url
            self.session = None
            self.cache = {}

            logger.info(f"GitHubRepositoryInfo initialized at {datetime.now()}")

        except Exception as e:
            logger.error(f"GitHubRepositoryInfo initialization failed: {str(e)}")
            raise

    async def get_repository_info(
        self, owner: str, repo: str, use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get GitHub repository information with comprehensive validation

        Args:
            owner: Repository owner
            repo: Repository name
            use_cache: Whether to use cached results

        Returns:
            Dict containing repository information
        """
        try:
            # Input validation
            if not all([owner, repo]):
                raise ValidationError("Owner and repo are required")

            # Sanitize inputs
            owner = str(owner).strip()
            repo = str(repo).strip()

            # Check cache first
            cache_key = f"{owner}/{repo}"
            if use_cache and cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if (
                    datetime.now() - cached_data["timestamp"]
                ).seconds < 300:  # 5 minutes
                    logger.info(f"Using cached data for {cache_key}")
                    return cached_data["data"]

            # Create session if needed
            if not self.session:
                await self._create_session()

            # Get repository information
            response = await self._make_api_call(
                method="GET", endpoint=f"/repos/{owner}/{repo}"
            )

            # Process and enrich data
            repo_info = self._process_repository_data(response)

            # Cache the result
            if use_cache:
                self.cache[cache_key] = {"data": repo_info, "timestamp": datetime.now()}

            logger.info(f"Repository info retrieved successfully for {owner}/{repo}")

            return repo_info

        except ValidationError as e:
            logger.error(f"Repository info validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Repository info unexpected error: {str(e)}")
            raise APIError(
                f"Unexpected error during repository info retrieval: {str(e)}"
            )

    def _process_repository_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enrich repository data"""
        try:
            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "owner": {
                    "login": data.get("owner", {}).get("login"),
                    "id": data.get("owner", {}).get("id"),
                    "type": data.get("owner", {}).get("type"),
                },
                "private": data.get("private", False),
                "html_url": data.get("html_url"),
                "clone_url": data.get("clone_url"),
                "ssh_url": data.get("ssh_url"),
                "default_branch": data.get("default_branch"),
                "language": data.get("language"),
                "size": data.get("size"),
                "stargazers_count": data.get("stargazers_count"),
                "watchers_count": data.get("watchers_count"),
                "forks_count": data.get("forks_count"),
                "open_issues_count": data.get("open_issues_count"),
                "has_issues": data.get("has_issues"),
                "has_projects": data.get("has_projects"),
                "has_wiki": data.get("has_wiki"),
                "has_pages": data.get("has_pages"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "pushed_at": data.get("pushed_at"),
                "retrieved_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Repository data processing failed: {str(e)}")
            raise ValidationError(f"Repository data processing failed: {str(e)}")

    async def _create_session(self):
        """Create secure HTTP session"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

            connector = aiohttp.TCPConnector(
                ssl=ssl_context, limit=100, limit_per_host=30, ttl_dns_cache=300
            )

            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHubIntegration/1.0",
            }

            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            )

        except Exception as e:
            logger.error(f"Session creation failed: {str(e)}")
            raise AuthenticationError(f"Session creation failed: {str(e)}")

    async def _make_api_call(
        self, method: str, endpoint: str, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make authenticated API call with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"

            async with self.session.request(
                method=method, url=url, json=data
            ) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_api_call(method, endpoint, data)

                if response.status == 401:
                    raise AuthenticationError("Invalid GitHub token")

                if response.status == 404:
                    raise APIError("Repository not found")

                if response.status >= 400:
                    error_data = await response.json()
                    raise APIError(
                        f"API call failed: {error_data.get('message', 'Unknown error')}"
                    )

                return await response.json()

        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            raise APIError(f"API call failed: {str(e)}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


# Custom exceptions
class ValidationError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class APIError(Exception):
    pass


class SecurityError(Exception):
    pass
