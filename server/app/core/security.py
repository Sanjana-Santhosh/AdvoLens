from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.core.auth import decode_token
from app.models.user import Department, User, UserRole

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _auth_disabled() -> bool:
    return os.getenv("AUTH_DISABLED", "true").lower() in {"1", "true", "yes", "on"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that extracts and validates the JWT token,
    then returns the current user.
    """
    if _auth_disabled():
        super_admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        if super_admin:
            return super_admin

        first_user = db.query(User).first()
        if first_user:
            return first_user

        # Fallback for fresh DBs with no users.
        return User(
            id=0,
            email="dev@advolens.local",
            hashed_password="",
            name="Auth Disabled",
            role=UserRole.SUPER_ADMIN,
            department=Department.OTHER,
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception
    
    # Decode the token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract email from token
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that ensures the user is active.
    Can be extended to check for disabled users.
    """
    # Add any additional checks here (e.g., is_active field)
    return current_user
