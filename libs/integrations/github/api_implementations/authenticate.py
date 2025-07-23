#!/usr/bin/env python3
"""
GitHub Authentication API Implementation
Iron Will 95% Compliance - Error Handling & Security Enhanced
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

def validate_github_token(token: str) -> None:
    """
    Validate GitHub token format
    
    Args:
        token: GitHub personal access token
        
    Raises:
        ValueError: If token format is invalid
    """
    if not token or not token.strip():
        raise ValueError("Token cannot be None or empty")
    
    token = token.strip()
    
    # GitHub personal access token format validation
    if not token.startswith('ghp_'):
        raise ValueError("Invalid GitHub token format")
    
    if len(token) < 40 or len(token) > 100:
        raise ValueError("Invalid GitHub token format")
    
    # Check for invalid characters (basic alphanumeric + underscore)
    if not re.match(r'^ghp_[A-Za-z0-9_]+$', token):
        raise ValueError("Invalid GitHub token format")

async def authenticate_user(token: str) -> Dict[str, Any]:
    """
    Authenticate user with GitHub API
    
    Args:
        token: GitHub personal access token
        
    Returns:
        Dict containing authentication result
    """
    try:
        # Input validation
        validate_github_token(token)
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ElderFlowAI/1.0"
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://api.github.com/user", headers=headers) as response:
                status_code = response.status
                
                try:
                    response_data = await response.json()
                except json.JSONDecodeError as e:
                    response_text = await response.text()
                    logger.error(f"Failed to parse JSON response: {e}")
                    return {
                        "success": False,
                        "error": f"Failed to parse API response: {response_text[:200]}",
                        "error_type": "ParseError",
                        "status_code": status_code
                    }
                
                if status_code == 200:
                    return {
                        "success": True,
                        "user": {
                            "login": response_data.get("login"),
                            "id": response_data.get("id"),
                            "name": response_data.get("name"),
                            "email": response_data.get("email"),
                            "plan": response_data.get("plan", {})
                        },
                        "status_code": status_code
                    }
                elif status_code == 401:
                    return {
                        "success": False,
                        "error": response_data.get("message", "Authentication failed"),
                        "status_code": status_code
                    }
                elif status_code == 403:
                    # Rate limiting
                    retry_after = None
                    if not ("X-RateLimit-Reset" in response.headers):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "X-RateLimit-Reset" in response.headers:
                        retry_after = int(response.headers["X-RateLimit-Reset"])
                    
                    return {
                        "success": False,
                        "error": response_data.get("message", "API rate limit exceeded"),
                        "status_code": status_code,
                        "retry_after": retry_after
                    }
                else:
                    return {
                        "success": False,
                        "error": response_data.get("message", f"API error: {status_code}"),
                        "status_code": status_code
                    }
                    
    except asyncio.TimeoutError:
        logger.error("Request timeout during authentication")
        return {
            "success": False,
            "error": "Request timeout - network error",
            "error_type": "NetworkError"
        }
    except aiohttp.ClientError as e:
        logger.error(f"Network error during authentication: {e}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "error_type": "NetworkError"
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "UnexpectedError"
        }