from typing import Dict, Optional
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    services: Dict[str, ServiceStatus]
    timestamp: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    redis: str
    app: str
    timestamp: str


class MetricsResponse(BaseModel):
    app_name: str
    version: str
    uptime_seconds: float
    total_requests: int
    error_requests: int
    active_websockets: int
    system_status: str
    timestamp: str
