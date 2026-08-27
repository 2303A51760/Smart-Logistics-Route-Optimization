from typing import Dict, Any, Optional
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
