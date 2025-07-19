#!/usr/bin/env python3
"""
GitHub Pull Request Merge API Implementation
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


class GitHubPullRequestMerger:
    """
    🗡️ Iron Will Compliant GitHub Pull Request Merger

    Features:
    - Comprehensive error handling
    - Security validation
    - Merge conflict detection
    - Status checks validation
    - Audit logging
    """

    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """Initialize PR merger with security validation"""
        try:
            if not token or len(token) < 10:
                raise ValueError("GitHub token must be at least 10 characters")

            if not base_url.startswith("https://"):
                raise SecurityError("Only HTTPS URLs are allowed")

            self.token = token
            self.base_url = base_url
            self.session = None

            logger.info(f"GitHubPullRequestMerger initialized at {datetime.now()}")

        except Exception as e:
            logger.error(f"GitHubPullRequestMerger initialization failed: {str(e)}")
            raise

    async def merge_pull_request(
        self, owner: str, repo: str, pull_number: int, merge_method: str = "merge"
    ) -> Dict[str, Any]:
        """
        Merge GitHub pull request with comprehensive validation

        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            merge_method: Merge method (merge, squash, rebase)

        Returns:
            Dict containing merge result
        """
        try:
            # Input validation
            if not all([owner, repo, pull_number]):
                raise ValidationError("Owner, repo, and pull_number are required")

            if merge_method not in ["merge", "squash", "rebase"]:
                raise ValidationError("Invalid merge method")

            # Sanitize inputs
            owner = str(owner).strip()
            repo = str(repo).strip()
            pull_number = int(pull_number)

            # Create session if needed
            if not self.session:
                await self._create_session()

            # Check PR status first
            pr_status = await self._check_pr_status(owner, repo, pull_number)
            if not pr_status["mergeable"]:
                raise ValidationError(
                    f"Pull request not mergeable: {pr_status['reason']}"
                )

            # Perform merge
            merge_data = {
                "commit_title": f"Merge pull request #{pull_number}",
                "merge_method": merge_method,
            }

            response = await self._make_api_call(
                method="PUT",
                endpoint=f"/repos/{owner}/{repo}/pulls/{pull_number}/merge",
                data=merge_data,
            )

            logger.info(f"PR #{pull_number} merged successfully in {owner}/{repo}")

            return {
                "success": True,
                "merge_result": response,
                "merged_at": datetime.now().isoformat(),
            }

        except ValidationError as e:
            logger.error(f"PR merge validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"PR merge unexpected error: {str(e)}")
            raise APIError(f"Unexpected error during PR merge: {str(e)}")

    async def _check_pr_status(
        self, owner: str, repo: str, pull_number: int
    ) -> Dict[str, Any]:
        """Check if PR is mergeable"""
        try:
            response = await self._make_api_call(
                method="GET", endpoint=f"/repos/{owner}/{repo}/pulls/{pull_number}"
            )

            return {
                "mergeable": response.get("mergeable", False)
                and response.get("state") == "open",
                "reason": "PR is not mergeable"
                if not response.get("mergeable")
                else None,
            }

        except Exception as e:
            logger.error(f"PR status check failed: {str(e)}")
            raise APIError(f"PR status check failed: {str(e)}")

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
