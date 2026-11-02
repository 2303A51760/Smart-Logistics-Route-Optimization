from typing import List, Union, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Smart Logistics & Route Optimization Platform"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    APP_ENV: Optional[str] = None
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Clearly-marked dev defaults only for development
    SECRET_KEY: str = "dev-insecure-secret-key-for-local-testing-only-32chars"
    JWT_SECRET_KEY: str = "dev-insecure-jwt-key-for-local-testing-only-32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:5173"

    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "smart_logistics"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/smart_logistics"

    # Database Connection Pool Tuning
    POSTGRES_POOL_SIZE: int = 20
    POSTGRES_MAX_OVERFLOW: int = 10
    POSTGRES_POOL_TIMEOUT: int = 30
    POSTGRES_POOL_RECYCLE: int = 1800

    # Redis Cache & Broker
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Phase 14 AI Configuration
    AI_ENABLED: bool = True
    AI_DEFAULT_MODEL: str = "logistics-ai-ensemble"
    AI_DELAY_THRESHOLD: float = 0.6
    AI_PRIORITY_THRESHOLD: float = 70.0
    AI_REOPTIMIZATION_THRESHOLD: float = 10.0  # Time saved in minutes to suggest re-optimization
    FUEL_COST_PER_LITER: float = 1.45  # Standard fuel cost estimate per liter
    AVG_FUEL_CONSUMPTION_L_PER_100KM: float = 12.5  # Fleet baseline fuel rate

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    CORS_ORIGINS: Optional[Union[str, List[str]]] = None

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env = (self.ENVIRONMENT or self.APP_ENV or "").lower()
        if env == "production":
            insecure_secret_indicators = [
                "change-in-production",
                "supersecret",
                "dev-insecure",
                "generate-a-strong",
                "placeholder",
            ]
            insecure_exact_secrets = {"secret", "changeme", "password", "admin", "123456"}

            # 1. Check SECRET_KEY
            if (
                not self.SECRET_KEY
                or len(self.SECRET_KEY) < 32
                or self.SECRET_KEY.lower() in insecure_exact_secrets
                or any(ind in self.SECRET_KEY.lower() for ind in insecure_secret_indicators)
            ):
                raise ValueError(
                    "Production security failure: SECRET_KEY must be set to a cryptographically secure random string of at least 32 characters, and cannot use default/placeholder values."
                )

            # 2. Check JWT_SECRET_KEY
            if (
                not self.JWT_SECRET_KEY
                or len(self.JWT_SECRET_KEY) < 32
                or self.JWT_SECRET_KEY.lower() in insecure_exact_secrets
                or any(ind in self.JWT_SECRET_KEY.lower() for ind in insecure_secret_indicators)
            ):
                raise ValueError(
                    "Production security failure: JWT_SECRET_KEY must be set to a cryptographically secure random string of at least 32 characters, and cannot use default/placeholder values."
                )

            # 3. Check Database Password
            insecure_db_passwords = {"postgres", "password", "changeme", "admin", "root", "123456", "your_secure_db_password_here"}
            if not self.POSTGRES_PASSWORD or self.POSTGRES_PASSWORD.lower() in insecure_db_passwords:
                raise ValueError(
                    "Production security failure: POSTGRES_PASSWORD cannot be default or placeholder ('postgres', 'password', etc.). Set a strong database password."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()

# Synchronize APP_ENV with ENVIRONMENT
if settings.APP_ENV and not settings.ENVIRONMENT:
    settings.ENVIRONMENT = settings.APP_ENV
elif settings.ENVIRONMENT and not settings.APP_ENV:
    settings.APP_ENV = settings.ENVIRONMENT

# Synchronize CORS_ORIGINS with BACKEND_CORS_ORIGINS if supplied
if settings.CORS_ORIGINS:
    if isinstance(settings.CORS_ORIGINS, str):
        settings.BACKEND_CORS_ORIGINS = [i.strip() for i in settings.CORS_ORIGINS.split(",") if i.strip()]
    elif isinstance(settings.CORS_ORIGINS, list):
        settings.BACKEND_CORS_ORIGINS = settings.CORS_ORIGINS
