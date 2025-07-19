#!/usr/bin/env python3
"""
GitHub Pull Requests List API Implementation
Iron Will 95% Compliance - Error Handling & Security Enhanced
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import ssl

logger = logging.getLogger(__name__)

class GitHubPullRequestsList:
    """
    🗡️ Iron Will Compliant GitHub Pull Requests List Retriever
    
    Features:
    - Comprehensive error handling
    - Security validation
    - Pagination support
    - Filtering capabilities
    - Audit logging
    """
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """Initialize pull requests list retriever with security validation"""
        try:
            if not token or len(token) < 10:
                raise ValueError("GitHub token must be at least 10 characters")
            
            if not base_url.startswith("https://"):
                raise SecurityError("Only HTTPS URLs are allowed")
            
            self.token = token
            self.base_url = base_url
            self.session = None
            
            logger.info(f"GitHubPullRequestsList initialized at {datetime.now()}")
            
        except Exception as e:
            logger.error(f"GitHubPullRequestsList initialization failed: {str(e)}")
            raise
    
    async def list_pull_requests(self, owner: str, repo: str, 
                                state: str = "open", 
                                sort: str = "created",
                                direction: str = "desc",
                                per_page: int = 30,
                                page: int = 1) -> Dict[str, Any]:
        """
        List GitHub pull requests with comprehensive validation
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            sort: Sort criteria (created, updated, popularity)
            direction: Sort direction (asc, desc)
            per_page: Number of PRs per page
            page: Page number
            
        Returns:
            Dict containing pull requests list and metadata
        """
        try:
            # Input validation
            if not all([owner, repo]):
                raise ValidationError("Owner and repo are required")
            
            if state not in ["open", "closed", "all"]:
                raise ValidationError("State must be 'open', 'closed', or 'all'")
            
            if sort not in ["created", "updated", "popularity"]:
                raise ValidationError("Sort must be 'created', 'updated', or 'popularity'")
            
            if direction not in ["asc", "desc"]:
                raise ValidationError("Direction must be 'asc' or 'desc'")
            
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
            params = {
                "state": state,
                "sort": sort,
                "direction": direction,
                "per_page": per_page,
                "page": page
            }
            
            # Get pull requests
            response = await self._make_api_call(
                method="GET",
                endpoint=f"/repos/{owner}/{repo}/pulls",
                params=params
            )
            
            # Process pull requests data
            processed_prs = [self._process_pr_data(pr) for pr in response["data"]]
            
            result = {
                "pull_requests": processed_prs,
                "total_count": len(processed_prs),
                "page": page,
                "per_page": per_page,
                "has_next": len(processed_prs) == per_page,
                "retrieved_at": datetime.now().isoformat()
            }
            
            logger.info(f"Pull requests retrieved successfully for {owner}/{repo}: {len(processed_prs)} PRs")
            
            return result
            
        except ValidationError as e:
            logger.error(f"Pull requests list validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Pull requests list unexpected error: {str(e)}")
            raise APIError(f"Unexpected error during pull requests list retrieval: {str(e)}")
    
    def _process_pr_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enrich pull request data"""
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
                    "type": data.get("user", {}).get("type")
                },
                "head": {
                    "ref": data.get("head", {}).get("ref"),
                    "sha": data.get("head", {}).get("sha"),
                    "repo": {
                        "full_name": data.get("head", {}).get("repo", {}).get("full_name")
                    } if data.get("head", {}).get("repo") else None
                },
                "base": {
                    "ref": data.get("base", {}).get("ref"),
                    "sha": data.get("base", {}).get("sha"),
                    "repo": {
                        "full_name": data.get("base", {}).get("repo", {}).get("full_name")
                    } if data.get("base", {}).get("repo") else None
                },
                "labels": [
                    {
                        "name": label.get("name"),
                        "color": label.get("color"),
                        "description": label.get("description")
                    }
                    for label in data.get("labels", [])
                ],
                "assignees": [
                    {
                        "login": assignee.get("login"),
                        "id": assignee.get("id")
                    }
                    for assignee in data.get("assignees", [])
                ],
                "milestone": {
                    "title": data.get("milestone", {}).get("title"),
                    "number": data.get("milestone", {}).get("number"),
                    "state": data.get("milestone", {}).get("state")
                } if data.get("milestone") else None,
                "draft": data.get("draft", False),
                "mergeable": data.get("mergeable"),
                "mergeable_state": data.get("mergeable_state"),
                "merged": data.get("merged", False),
                "merged_at": data.get("merged_at"),
                "comments": data.get("comments"),
                "review_comments": data.get("review_comments"),
                "commits": data.get("commits"),
                "additions": data.get("additions"),
                "deletions": data.get("deletions"),
                "changed_files": data.get("changed_files"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "closed_at": data.get("closed_at"),
                "html_url": data.get("html_url")
            }
            
        except Exception as e:
            logger.error(f"PR data processing failed: {str(e)}")
            raise ValidationError(f"PR data processing failed: {str(e)}")
    
    async def _create_session(self):
        """Create secure HTTP session"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            
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
    
    async def _make_api_call(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated API call with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            async with self.session.request(
                method=method,
                url=url,
                params=params
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
                    raise APIError(f"API call failed: {error_data.get('message', 'Unknown error')}")
                
                data = await response.json()
                
                return {
                    "data": data,
                    "headers": dict(response.headers)
                }
                
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
