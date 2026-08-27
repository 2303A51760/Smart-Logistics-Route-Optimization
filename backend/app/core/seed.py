from datetime import datetime
from typing import Dict
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Pre-computed bcrypt hashes for demo passwords:
# admin@example.com -> Admin@123456
# manager@example.com -> Manager@123456
# driver@example.com -> Driver@123456
SEED_USERS: Dict[str, dict] = {
    "admin@example.com": {
        "id": "usr-admin-001",
        "name": "System Administrator",
        "email": "admin@example.com",
        "password_hash": get_password_hash("Admin@123456"),
        "role": UserRole.ADMIN.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "manager@example.com": {
        "id": "usr-mgr-002",
        "name": "Logistics Dispatch Manager",
        "email": "manager@example.com",
        "password_hash": get_password_hash("Manager@123456"),
        "role": UserRole.LOGISTICS_MANAGER.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    "driver@example.com": {
        "id": "usr-drv-003",
        "name": "David Driver (NYC)",
        "email": "driver@example.com",
        "password_hash": get_password_hash("Driver@123456"),
        "role": UserRole.DRIVER.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
}
