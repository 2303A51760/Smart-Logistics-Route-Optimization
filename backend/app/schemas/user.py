from typing import Optional
from datetime import datetime
import enum
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    LOGISTICS_MANAGER = "LOGISTICS_MANAGER"
    DRIVER = "DRIVER"


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Alex Logistics")
    email: EmailStr = Field(..., example="manager@example.com")
    role: UserRole = Field(default=UserRole.DRIVER, example=UserRole.LOGISTICS_MANAGER)
    is_active: bool = True


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Alex Logistics")
    email: EmailStr = Field(..., example="manager@example.com")
    password: str = Field(..., min_length=6, max_length=100, example="SecurePass123!")
    role: Optional[UserRole] = Field(default=UserRole.DRIVER)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="admin@example.com")
    password: str = Field(..., example="Admin@123456")


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str
