import hashlib
import secrets
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Dict
from typing import Optional

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import jwt
from jose import JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..models.auth import PermissionType
from ..models.auth import User
from ..models.auth import UserRole

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class SecurityManager:
    """Comprehensive security manager for Elders Guild Web"""

    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_EXPIRE_MINUTES

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, user_id: int) -> str:
        """Create refresh token for token renewal"""
        data = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
            "iat": datetime.now(timezone.utc),
        }

        encoded_jwt = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("type") != token_type:
                return None

            return payload
        except JWTError:
            return None

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token tied to session"""
        data = f"{session_id}{datetime.now(timezone.utc).isoformat()}{self.secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()

    def create_device_fingerprint(self, request: Request) -> str:
        """Create device fingerprint for security tracking"""
        user_agent = request.headers.get("user-agent", "")
        accept_language = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")

        fingerprint_data = f"{user_agent}{accept_language}{accept_encoding}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()


security_manager = SecurityManager()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    payload = security_manager.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")

    if user.is_locked():
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="User account is temporarily locked")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    return current_user


class RoleChecker:
    """Check user role and permissions"""

    def __init__(self, required_role: UserRole):
        self.required_role = required_role

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        role_hierarchy = {UserRole.SERVANT: 0, UserRole.SAGE: 1, UserRole.ELDER: 2, UserRole.GRAND_ELDER: 3}

        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(self.required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required role: {self.required_role.value}",
            )

        return current_user


class PermissionChecker:
    """Check specific user permissions"""

    def __init__(self, required_permission: PermissionType):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_permission(self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {self.required_permission.value}",
            )

        return current_user


# Common role dependencies
require_grand_elder = RoleChecker(UserRole.GRAND_ELDER)
require_elder = RoleChecker(UserRole.ELDER)
require_sage = RoleChecker(UserRole.SAGE)

# Common permission dependencies
require_elder_council = PermissionChecker(PermissionType.ELDER_COUNCIL)
require_sage_management = PermissionChecker(PermissionType.SAGE_MANAGEMENT)
require_monitoring = PermissionChecker(PermissionType.MONITORING)


class SecurityHeaders:
    """Security headers middleware"""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get comprehensive security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: ws:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none';"
            ),
        }
