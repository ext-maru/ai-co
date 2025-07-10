from datetime import datetime
from enum import Enum

from passlib.context import CryptContext
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """Elder hierarchy system"""

    GRAND_ELDER = "grand_elder"  # 最高権限 - システム全体管理
    ELDER = "elder"  # 高権限 - 評議会メンバー
    SAGE = "sage"  # 中権限 - 4賢者システム
    SERVANT = "servant"  # 基本権限 - 一般ユーザー


class PermissionType(str, Enum):
    """Permission types for granular access control"""

    SYSTEM_ADMIN = "system_admin"
    ELDER_COUNCIL = "elder_council"
    SAGE_MANAGEMENT = "sage_management"
    DATA_ACCESS = "data_access"
    API_ACCESS = "api_access"
    WEBSOCKET_ACCESS = "websocket_access"
    MONITORING = "monitoring"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)

    # Elder hierarchy
    role = Column(SQLEnum(UserRole), default=UserRole.SERVANT, nullable=False)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # OAuth fields
    oauth_provider = Column(String)  # google, github, etc.
    oauth_id = Column(String)

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str):
        """Set user password with hashing"""
        self.hashed_password = pwd_context.hash(password)

    def has_permission(self, permission: PermissionType) -> bool:
        """Check if user has specific permission"""
        # Grand Elder has all permissions
        if self.role == UserRole.GRAND_ELDER:
            return True

        # Role-based permissions
        role_permissions = {
            UserRole.ELDER: [
                PermissionType.ELDER_COUNCIL,
                PermissionType.SAGE_MANAGEMENT,
                PermissionType.DATA_ACCESS,
                PermissionType.API_ACCESS,
                PermissionType.WEBSOCKET_ACCESS,
                PermissionType.MONITORING,
            ],
            UserRole.SAGE: [PermissionType.DATA_ACCESS, PermissionType.API_ACCESS, PermissionType.WEBSOCKET_ACCESS],
            UserRole.SERVANT: [PermissionType.API_ACCESS],
        }

        if permission in role_permissions.get(self.role, []):
            return True

        # Check explicit permissions
        return any(up.permission == permission for up in self.permissions)

    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    refresh_token = Column(String, unique=True, index=True)

    # Session metadata
    ip_address = Column(String)
    user_agent = Column(String)
    device_fingerprint = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # Security
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="sessions")


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(SQLEnum(PermissionType), nullable=False)

    # Metadata
    granted_by = Column(Integer, ForeignKey("users.id"))
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="permissions", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, unique=True, index=True, nullable=False)
    provider = Column(String, nullable=False)
    redirect_uri = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
