from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from pydantic import EmailStr
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.security import get_current_user
from ...core.security import security_manager
from ...core.security import SecurityHeaders
from ...models.auth import OAuthState
from ...models.auth import User
from ...models.auth import UserRole
from ...models.auth import UserSession

router = APIRouter()

# Pydantic models for requests/responses
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str = ""

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime = None

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.post("/register", response_model=UserProfile)
async def register_user(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register new user"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=UserRole.SERVANT  # Default role
    )
    user.set_password(user_data.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserProfile.from_orm(user)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """User login with JWT token generation"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    # Get user
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not user.verify_password(form_data.password):
        # Increment failed login attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to failed login attempts"
        )

    # Reset failed login attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()

    # Create tokens
    access_token = security_manager.create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )
    refresh_token = security_manager.create_refresh_token(user.id)

    # Create session
    session = UserSession(
        user_id=user.id,
        session_token=security_manager.generate_session_token(),
        refresh_token=refresh_token,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        device_fingerprint=security_manager.create_device_fingerprint(request),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )

    db.add(session)
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    # Verify refresh token
    payload = security_manager.verify_token(refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = int(payload.get("sub"))

    # Check session
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.is_active == True
    ).first()

    if not session or session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive"
        )

    # Create new tokens
    access_token = security_manager.create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )
    new_refresh_token = security_manager.create_refresh_token(user.id)

    # Update session
    session.refresh_token = new_refresh_token
    session.last_accessed = datetime.utcnow()
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """User logout - invalidate all sessions"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    # Invalidate all user sessions
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).update({"is_active": False, "revoked_at": datetime.utcnow()})

    db.commit()

    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    response: Response = None
):
    """Get current user profile"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    return UserProfile.from_orm(current_user)

@router.put("/me", response_model=UserProfile)
async def update_profile(
    profile_update: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """Update user profile"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    # Update allowed fields
    allowed_fields = {"full_name", "email"}
    for field, value in profile_update.items():
        if field in allowed_fields and hasattr(current_user, field):
            setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return UserProfile.from_orm(current_user)

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    # Verify current password
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )

    # Update password
    current_user.set_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()

    # Invalidate all sessions except current
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).update({"is_active": False, "revoked_at": datetime.utcnow()})

    db.commit()

    return {"message": "Password changed successfully"}

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()

    return [
        {
            "id": session.id,
            "created_at": session.created_at,
            "last_accessed": session.last_accessed,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent
        }
        for session in sessions
    ]

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """Revoke specific session"""
    # Add security headers
    for key, value in SecurityHeaders.get_security_headers().items():
        response.headers[key] = value

    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.is_active = False
    session.revoked_at = datetime.utcnow()
    db.commit()

    return {"message": "Session revoked successfully"}
