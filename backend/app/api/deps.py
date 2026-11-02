import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate user from JWT access token using users table."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except (jwt.PyJWTError, Exception) as e:
        logger.warning(f"JWT decode error: {e}")
        raise credentials_exception

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user account",
                )
            return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error during user authentication: {e}", exc_info=True)
        raise credentials_exception

    raise credentials_exception


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Only ADMIN role can access."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )
    return current_user


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    """ADMIN and LOGISTICS_MANAGER roles can access."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.LOGISTICS_MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin privileges required for this operation",
        )
    return current_user


def require_driver(current_user: User = Depends(get_current_user)) -> User:
    """ADMIN, LOGISTICS_MANAGER, and DRIVER roles can access."""
    if current_user.role not in [
        UserRole.ADMIN.value,
        UserRole.LOGISTICS_MANAGER.value,
        UserRole.DRIVER.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver access required for this operation",
        )
    return current_user
