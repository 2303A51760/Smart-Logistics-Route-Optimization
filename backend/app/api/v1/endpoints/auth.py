import uuid
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from app.api.deps import (
    get_current_user,
    require_admin,
    require_manager,
    require_driver,
)
from app.services.audit_service import audit_service
from app.core.rate_limiter import check_rate_limit
from app.api.v1.endpoints.drivers import ensure_driver_profile

router = APIRouter()


def _get_client_info(request: Request) -> tuple[str, str]:
    """Helper to extract client IP and User-Agent safely from HTTP request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "Unknown Client")
    return ip, user_agent[:250]


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account directly in PostgreSQL."""
    if request:
        await check_rate_limit(request)
    ip, ua = _get_client_info(request) if request else ("127.0.0.1", "Internal")

    email_lower = user_in.email.lower()

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email_lower))
    if result.scalar_one_or_none():
        await audit_service.log_event(
            action="REGISTRATION_FAILED",
            user_email=email_lower,
            resource_type="AUTH",
            ip_address=ip,
            user_agent=ua,
            success=False,
            details={"reason": "User already exists", "email": email_lower},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(user_in.password)
    user_role = user_in.role.value if user_in.role else UserRole.DRIVER.value
    now = datetime.utcnow()

    new_user = User(
        id=user_id,
        name=user_in.name,
        email=email_lower,
        password_hash=hashed_pwd,
        role=user_role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Automatically create/link Driver profile if registering with role DRIVER
    if user_role in (UserRole.DRIVER.value, UserRole.DRIVER):
        await ensure_driver_profile(
            user_id=user_id,
            user_name=user_in.name,
            db=db,
        )

    # Log successful registration
    await audit_service.log_event(
        action="USER_REGISTER",
        user_id=user_id,
        user_email=email_lower,
        user_role=user_role,
        resource_type="USER",
        resource_id=user_id,
        ip_address=ip,
        user_agent=ua,
        success=True,
        details={"name": user_in.name, "role": user_role},
        db=db,
    )

    access_token = create_access_token(subject=user_id, role=user_role, name=user_in.name)
    refresh_token = create_refresh_token(subject=user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            name=user_in.name,
            email=email_lower,
            role=UserRole(user_role),
            is_active=True,
            created_at=now,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with email and password using users table."""
    if request:
        await check_rate_limit(request)
    ip, ua = _get_client_info(request) if request else ("127.0.0.1", "Internal")

    email_lower = login_data.email.lower()

    result = await db.execute(select(User).where(User.email == email_lower))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        await audit_service.log_event(
            action="LOGIN_FAILED",
            user_id=user.id if user else None,
            user_email=email_lower,
            user_role=user.role if user else None,
            resource_type="AUTH",
            ip_address=ip,
            user_agent=ua,
            success=False,
            details={"reason": "Invalid credentials", "email": email_lower},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        await audit_service.log_event(
            action="LOGIN_BLOCKED_INACTIVE",
            user_id=user.id,
            user_email=email_lower,
            user_role=user.role,
            resource_type="AUTH",
            ip_address=ip,
            user_agent=ua,
            success=False,
            details={"reason": "Account is inactive"},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Please contact administrator.",
        )

    # Log successful login
    await audit_service.log_event(
        action="USER_LOGIN",
        user_id=user.id,
        user_email=user.email,
        user_role=user.role,
        resource_type="AUTH",
        resource_id=user.id,
        ip_address=ip,
        user_agent=ua,
        success=True,
        details={"login_time": datetime.utcnow().isoformat()},
        db=db,
    )

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        name=user.name,
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=UserRole(user.role),
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_access_token(
    req: RefreshTokenRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Issue a new access token using a valid refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        payload = decode_token(req.refresh_token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not user_id or token_type != "refresh":
            raise credentials_exception
    except (jwt.PyJWTError, Exception):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    ip, ua = _get_client_info(request) if request else ("127.0.0.1", "Internal")
    await audit_service.log_event(
        action="TOKEN_REFRESH",
        user_id=user.id,
        user_email=user.email,
        user_role=user.role,
        resource_type="AUTH",
        ip_address=ip,
        user_agent=ua,
        success=True,
        details={"token_type": "access_token_renewed"},
        db=db,
    )

    new_access_token = create_access_token(
        subject=user.id,
        role=user.role,
        name=user.name,
    )
    new_refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve details for the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=UserRole(current_user.role),
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/logout")
async def logout(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log out current user and record audit event."""
    ip, ua = _get_client_info(request) if request else ("127.0.0.1", "Internal")
    await audit_service.log_event(
        action="USER_LOGOUT",
        user=current_user,
        resource_type="AUTH",
        resource_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
        success=True,
        details={"logout_time": datetime.utcnow().isoformat()},
        db=db,
    )
    return {
        "status": "success",
        "message": f"User {current_user.email} successfully logged out",
    }


# RBAC Protected Test Routes
@router.get("/admin-only")
async def admin_only_endpoint(current_user: User = Depends(require_admin)):
    """Protected endpoint strictly requiring ADMIN role."""
    return {
        "message": "Admin authorization verified",
        "user_email": current_user.email,
        "role": current_user.role,
        "permissions": ["FULL_ACCESS", "SYSTEM_SETTINGS", "USER_MANAGEMENT"],
    }


@router.get("/manager-only")
async def manager_only_endpoint(current_user: User = Depends(require_manager)):
    """Protected endpoint requiring LOGISTICS_MANAGER or ADMIN role."""
    return {
        "message": "Manager authorization verified",
        "user_email": current_user.email,
        "role": current_user.role,
        "permissions": ["FLEET_DISPATCH", "ROUTE_OPTIMIZATION", "ORDER_MANAGEMENT"],
    }


@router.get("/driver-only")
async def driver_only_endpoint(current_user: User = Depends(require_driver)):
    """Protected endpoint accessible by DRIVER, LOGISTICS_MANAGER, and ADMIN."""
    return {
        "message": "Driver authorization verified",
        "user_email": current_user.email,
        "role": current_user.role,
        "permissions": ["ASSIGNED_ROUTES", "TELEMETRY_STREAM", "DELIVERY_STATUS_UPDATE"],
    }
