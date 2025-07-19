#!/usr/bin/env python3
"""
GitHub Integration Input Validator
Iron Will 95% Compliance - Comprehensive Input Validation
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class GitHubInputValidator:
    """
    🛡️ Iron Will Compliant Input Validator
    
    Features:
    - SQL injection prevention
    - XSS protection
    - Length validation
    - Format validation
    - Content filtering
    """
    
    def __init__(self):
        """Initialize input validator"""
        self.max_lengths = {
            "repo_name": 100,
            "description": 500,
            "title": 200,
            "body": 50000,
            "username": 39,
            "branch_name": 250
        }
        
        self.dangerous_patterns = [
            # SQL injection patterns
            r"('(''|[^'])*')",
            r'("(""|[^"])*")',
            r'\b(drop|delete|update|insert|create|alter|exec|execute)\b',
            r'\b(union|select|from|where|having|group\s+by|order\s+by)\b',
            
            # XSS patterns
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'javascript:',
            r'onclick\s*=',
            r'onerror\s*=',
            r'onload\s*=',
            
            # Command injection patterns
            r'(;|\||\&|\$\(|\`)',
            r'\b(rm|del|format|shutdown|reboot)\b',
            
            # Path traversal patterns
            r'(\.\./)|(\.\.\\)',
            r'/etc/passwd',
            r'/proc/self/environ'
        ]
        
    def validate_repository_name(self, name: str) -> bool:
        """Validate repository name"""
        try:
            if not isinstance(name, str):
                raise ValidationError("Repository name must be a string")
            
            if len(name) == 0 or len(name) > self.max_lengths["repo_name"]:
                raise ValidationError(f"Repository name must be 1-{self.max_lengths['repo_name']} characters")
            
            # GitHub repository name pattern - supports owner/repo format
            # Valid characters: alphanumeric, hyphens, underscores, dots, and forward slash
            if not re.match(r'^[a-zA-Z0-9._/-]+$', name):
                raise ValidationError("Repository name contains invalid characters")
            
            # Check if it's in owner/repo format
            if '/' in name:
                parts = name.split('/')
                if len(parts) != 2:
                    raise ValidationError("Repository name must be in 'owner/repo' format")
                
                owner, repo = parts
                if not owner or not repo:
                    raise ValidationError("Both owner and repository name must be non-empty")
                
                # Validate owner and repo parts separately
                for part in [owner, repo]:
                    if part.startswith('.') or part.endswith('.'):
                        raise ValidationError("Repository owner and name cannot start or end with a dot")
                    if part.startswith('-') or part.endswith('-'):
                        raise ValidationError("Repository owner and name cannot start or end with a hyphen")
            else:
                # Single repository name (without owner)
                if name.startswith('.') or name.endswith('.'):
                    raise ValidationError("Repository name cannot start or end with a dot")
                if name.startswith('-') or name.endswith('-'):
                    raise ValidationError("Repository name cannot start or end with a hyphen")
            
            # Check for dangerous patterns
            self._check_dangerous_patterns(name, "repository_name")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Repository name validation failed: {str(e)}")
            raise ValidationError(f"Repository name validation failed: {str(e)}")
    
    def validate_description(self, description: str) -> bool:
        """Validate repository description"""
        try:
            if not isinstance(description, str):
                raise ValidationError("Description must be a string")
            
            if len(description) > self.max_lengths["description"]:
                raise ValidationError(f"Description must be less than {self.max_lengths['description']} characters")
            
            # Check for dangerous patterns
            self._check_dangerous_patterns(description, "description")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Description validation failed: {str(e)}")
            raise ValidationError(f"Description validation failed: {str(e)}")
    
    def validate_issue_title(self, title: str) -> bool:
        """Validate issue title"""
        try:
            if not isinstance(title, str):
                raise ValidationError("Title must be a string")
            
            if len(title) == 0 or len(title) > self.max_lengths["title"]:
                raise ValidationError(f"Title must be 1-{self.max_lengths['title']} characters")
            
            # Check for dangerous patterns
            self._check_dangerous_patterns(title, "title")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Title validation failed: {str(e)}")
            raise ValidationError(f"Title validation failed: {str(e)}")
    
    def validate_issue_body(self, body: str) -> bool:
        """Validate issue body"""
        try:
            if not isinstance(body, str):
                raise ValidationError("Body must be a string")
            
            if len(body) > self.max_lengths["body"]:
                raise ValidationError(f"Body must be less than {self.max_lengths['body']} characters")
            
            # Check for dangerous patterns
            self._check_dangerous_patterns(body, "body")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Body validation failed: {str(e)}")
            raise ValidationError(f"Body validation failed: {str(e)}")
    
    def validate_username(self, username: str) -> bool:
        """Validate GitHub username"""
        try:
            if not isinstance(username, str):
                raise ValidationError("Username must be a string")
            
            if len(username) == 0 or len(username) > self.max_lengths["username"]:
                raise ValidationError(f"Username must be 1-{self.max_lengths['username']} characters")
            
            # GitHub username pattern
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', username):
                raise ValidationError("Username contains invalid characters")
            
            # Check for dangerous patterns
            self._check_dangerous_patterns(username, "username")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Username validation failed: {str(e)}")
            raise ValidationError(f"Username validation failed: {str(e)}")
    
    def validate_branch_name(self, branch_name: str) -> bool:
        """Validate branch name"""
        try:
            if not isinstance(branch_name, str):
                raise ValidationError("Branch name must be a string")
            
            if len(branch_name) == 0 or len(branch_name) > self.max_lengths["branch_name"]:
                raise ValidationError(f"Branch name must be 1-{self.max_lengths['branch_name']} characters")
            
            # Git branch name validation
            if not re.match(r'^[a-zA-Z0-9._/-]+$', branch_name):
                raise ValidationError("Branch name contains invalid characters")
            
            if branch_name.startswith('.') or branch_name.endswith('.'):
                raise ValidationError("Branch name cannot start or end with a dot")
            
            if '//' in branch_name or branch_name.startswith('/') or branch_name.endswith('/'):
                raise ValidationError("Invalid branch name format")
            
            # Check for dangerous patterns
            self._check_dangerous_patterns(branch_name, "branch_name")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Branch name validation failed: {str(e)}")
            raise ValidationError(f"Branch name validation failed: {str(e)}")
    
    def validate_token(self, token: str) -> bool:
        """Validate GitHub token"""
        try:
            if not isinstance(token, str):
                raise ValidationError("Token must be a string")
            
            if len(token) == 0:
                raise ValidationError("Token cannot be empty")
            
            # GitHub token patterns
            # Classic tokens start with ghp_
            # Fine-grained tokens start with github_pat_
            if not (token.startswith('ghp_') or token.startswith('github_pat_')):
                raise ValidationError("Invalid token format")
            
            # Check minimum length
            if len(token) < 40:
                raise ValidationError("Token too short")
            
            # Check for dangerous patterns
            self._check_dangerous_patterns(token, "token")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise ValidationError(f"Token validation failed: {str(e)}")
    
    def _check_dangerous_patterns(self, text: str, field_name: str):
        """Check for dangerous patterns in text"""
        try:
            text_lower = text.lower()
            
            for pattern in self.dangerous_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    logger.warning(f"Dangerous pattern detected in {field_name}: {pattern}")
                    raise SecurityError(f"Suspicious pattern detected in {field_name}")
            
        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Pattern checking failed: {str(e)}")
            raise ValidationError(f"Pattern checking failed: {str(e)}")
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text for safe usage"""
        try:
            if not isinstance(text, str):
                return str(text)
            
            # Remove null bytes
            text = text.replace('\x00', '')
            
            # Remove control characters except tab, newline, and carriage return
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
            
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Trim whitespace
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Text sanitization failed: {str(e)}")
            raise ValidationError(f"Text sanitization failed: {str(e)}")
    
    def validate_request_params(self, params: Dict[str, Any]) -> bool:
        """Validate request parameters"""
        try:
            if not isinstance(params, dict):
                raise ValidationError("Parameters must be a dictionary")
            
            # Check for required parameters
            required_params = ['repo_name', 'username']
            for param in required_params:
                if param not in params:
                    raise ValidationError(f"Missing required parameter: {param}")
            
            # Validate each parameter
            for key, value in params.items():
                if key == 'repo_name':
                    self.validate_repository_name(value)
                elif key == 'username':
                    self.validate_username(value)
                elif key == 'description':
                    self.validate_description(value)
                elif key == 'title':
                    self.validate_issue_title(value)
                elif key == 'body':
                    self.validate_issue_body(value)
                elif key == 'branch_name':
                    self.validate_branch_name(value)
                elif key == 'token':
                    self.validate_token(value)
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Parameter validation failed: {str(e)}")
            raise ValidationError(f"Parameter validation failed: {str(e)}")

class ValidationError(Exception):
    """Input validation error"""
    pass

class SecurityError(Exception):
    """Security-related error"""
    pass