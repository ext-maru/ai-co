#!/usr/bin/env python3
"""
GitHub Issues List API Implementation
Iron Will 95% Compliance - Error Handling & Security Enhanced
"""

import asyncio
import json
import logging
import ssl
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class GitHubIssuesList:
    """
    🗡️ Iron Will Compliant GitHub Issues List Retriever

    Features:
    - Comprehensive error handling
    - Security validation
    - Pagination support
    - Filtering capabilities
    - Audit logging
    """

    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """Initialize issues list retriever with security validation"""
        try:
            if not token or len(token) < 10:
                raise ValueError("GitHub token must be at least 10 characters")

            if not base_url.startswith("https://"):
                raise SecurityError("Only HTTPS URLs are allowed")

            self.token = token
            self.base_url = base_url
            self.session = None

            logger.info(f"GitHubIssuesList initialized at {datetime.now()}")

        except Exception as e:
            logger.error(f"GitHubIssuesList initialization failed: {str(e)}")
            raise

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        List GitHub issues with comprehensive validation

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            labels: List of labels to filter by
            per_page: Number of issues per page
            page: Page number

        Returns:
            Dict containing issues list and metadata
        """
        try:
            # Input validation
            if not all([owner, repo]):
                raise ValidationError("Owner and repo are required")

            if state not in ["open", "closed", "all"]:
                raise ValidationError("State must be 'open', 'closed', or 'all'")

            if per_page < 1 or per_page > 100:
                raise ValidationError("per_page must be between 1 and 100")

            if page < 1:
                raise ValidationError("page must be >= 1")

            # Sanitize inputs
            owner = str(owner).strip()
            repo = str(repo).strip()

            # Create session if needed
            if not self.session:
                await self._create_session()

            # Build query parameters
            params = {"state": state, "per_page": per_page, "page": page}

            if labels:
                params["labels"] = ",".join(labels)

            # Get issues
            response = await self._make_api_call(
                method="GET", endpoint=f"/repos/{owner}/{repo}/issues", params=params
            )

            # Process issues data
            processed_issues = [
                self._process_issue_data(issue) for issue in response["data"]
            ]

            result = {
                "issues": processed_issues,
                "total_count": len(processed_issues),
                "page": page,
                "per_page": per_page,
                "has_next": len(processed_issues) == per_page,
                "retrieved_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Issues retrieved successfully for {owner}/{repo}: {len(processed_issues)} issues"
            )

            return result

        except ValidationError as e:
            logger.error(f"Issues list validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Issues list unexpected error: {str(e)}")
            raise APIError(f"Unexpected error during issues list retrieval: {str(e)}")

    def _process_issue_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enrich issue data"""
        try:
            return {
                "id": data.get("id"),
                "number": data.get("number"),
                "title": data.get("title"),
                "body": data.get("body"),
                "state": data.get("state"),
                "user": {
                    "login": data.get("user", {}).get("login"),
                    "id": data.get("user", {}).get("id"),
                    "type": data.get("user", {}).get("type"),
                },
                "labels": [
                    {
                        "name": label.get("name"),
                        "color": label.get("color"),
                        "description": label.get("description"),
                    }
                    for label in data.get("labels", [])
                ],
                "assignees": [
                    {"login": assignee.get("login"), "id": assignee.get("id")}
                    for assignee in data.get("assignees", [])
                ],
                "milestone": (
                    {
                        "title": data.get("milestone", {}).get("title"),
                        "number": data.get("milestone", {}).get("number"),
                        "state": data.get("milestone", {}).get("state"),
                    }
                    if data.get("milestone")
                    else None
                ),
                "comments": data.get("comments"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "closed_at": data.get("closed_at"),
                "html_url": data.get("html_url"),
            }

        except Exception as e:
            logger.error(f"Issue data processing failed: {str(e)}")
            raise ValidationError(f"Issue data processing failed: {str(e)}")

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
        self, method: str, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make authenticated API call with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"

            async with self.session.request(
                method=method, url=url, params=params
            ) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_api_call(method, endpoint, params)

                if response.status == 401:
                    raise AuthenticationError("Invalid GitHub token")

                if response.status == 404:
                    raise APIError("Repository not found")

                if response.status >= 400:
                    error_data = await response.json()
                    raise APIError(
                        f"API call failed: {error_data.get('message', 'Unknown error')}"
                    )

                data = await response.json()

                return {"data": data, "headers": dict(response.headers)}

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
