import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, Boolean, DateTime
from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    LOGISTICS_MANAGER = "LOGISTICS_MANAGER"
    DRIVER = "DRIVER"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default=UserRole.DRIVER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
