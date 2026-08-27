import uuid
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.core.database import get_db, check_db_connection
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
from app.core.seed import SEED_USERS
from app.services.audit_service import audit_service
from app.core.rate_limiter import check_rate_limit

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
    """Register a new user account."""
    if request:
        await check_rate_limit(request)
    ip, ua = _get_client_info(request) if request else ("127.0.0.1", "Internal")

    email_lower = user_in.email.lower()
    
    # Check seed store
    if email_lower in SEED_USERS:
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

    # Check DB if connected
    if await check_db_connection():
        try:
            result = await db.execute(select(User).where(User.email == email_lower))
            if result.scalar_one_or_none():
                await audit_service.log_event(
                    action="REGISTRATION_FAILED",
                    user_email=email_lower,
                    resource_type="AUTH",
                    ip_address=ip,
                    user_agent=ua,
                    success=False,
                    details={"reason": "User already exists in database", "email": email_lower},
                    db=db,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email address already exists",
                )
        except HTTPException:
            raise
        except Exception:
            pass

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

    # Save to DB if online
    if await check_db_connection():
        try:
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
        except Exception:
            pass

    # Keep in in-memory seed registry for instant lookup
    SEED_USERS[email_lower] = {
        "id": user_id,
        "name": user_in.name,
        "email": email_lower,
        "password_hash": hashed_pwd,
        "role": user_role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

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
    """Authenticate user with email and password, returning JWT access & refresh tokens."""
    if request:
        await check_rate_limit(request)
    ip, ua = _get_client_info(request) if request else ("127.0.0.1", "Internal")

    email_lower = login_data.email.lower()
    user_record = None

    # Check DB first
    if await check_db_connection():
        try:
            result = await db.execute(select(User).where(User.email == email_lower))
            db_user = result.scalar_one_or_none()
            if db_user:
                user_record = {
                    "id": db_user.id,
                    "name": db_user.name,
                    "email": db_user.email,
                    "password_hash": db_user.password_hash,
                    "role": db_user.role,
                    "is_active": db_user.is_active,
                    "created_at": db_user.created_at,
                }
        except Exception:
            pass

    # Check seed store
    if not user_record and email_lower in SEED_USERS:
        user_record = SEED_USERS[email_lower]

    if not user_record or not verify_password(login_data.password, user_record["password_hash"]):
        await audit_service.log_event(
            action="LOGIN_FAILED",
            user_id=user_record["id"] if user_record else None,
            user_email=email_lower,
            user_role=user_record["role"] if user_record else None,
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

    if not user_record["is_active"]:
        await audit_service.log_event(
            action="LOGIN_BLOCKED_INACTIVE",
            user_id=user_record["id"],
            user_email=email_lower,
            user_role=user_record["role"],
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
        user_id=user_record["id"],
        user_email=user_record["email"],
        user_role=user_record["role"],
        resource_type="AUTH",
        resource_id=user_record["id"],
        ip_address=ip,
        user_agent=ua,
        success=True,
        details={"login_time": datetime.utcnow().isoformat()},
        db=db,
    )

    access_token = create_access_token(
        subject=user_record["id"],
        role=user_record["role"],
        name=user_record["name"],
    )
    refresh_token = create_refresh_token(subject=user_record["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(
            id=user_record["id"],
            name=user_record["name"],
            email=user_record["email"],
            role=UserRole(user_record["role"]),
            is_active=user_record["is_active"],
            created_at=user_record["created_at"],
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

    # Find user
    user_record = None
    if await check_db_connection():
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            db_user = result.scalar_one_or_none()
            if db_user:
                user_record = {
                    "id": db_user.id,
                    "name": db_user.name,
                    "role": db_user.role,
                    "is_active": db_user.is_active,
                }
        except Exception:
            pass

    if not user_record:
        for seed in SEED_USERS.values():
            if seed["id"] == user_id:
                user_record = seed
                break

    if not user_record or not user_record["is_active"]:
        raise credentials_exception

    ip, ua = _get_client_info(request) if request else ("127.0.0.1", "Internal")
    await audit_service.log_event(
        action="TOKEN_REFRESH",
        user_id=user_record["id"],
        user_email=user_record.get("email"),
        user_role=user_record["role"],
        resource_type="AUTH",
        ip_address=ip,
        user_agent=ua,
        success=True,
        details={"token_type": "access_token_renewed"},
        db=db,
    )

    new_access_token = create_access_token(
        subject=user_record["id"],
        role=user_record["role"],
        name=user_record["name"],
    )
    new_refresh_token = create_refresh_token(subject=user_record["id"])

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
