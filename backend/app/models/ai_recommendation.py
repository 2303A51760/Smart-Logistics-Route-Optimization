import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum, JSON, Text
from app.core.database import Base


class RecommendationType(str, enum.Enum):
    ASSIGN_ORDER = "ASSIGN_ORDER"
    REOPTIMIZE_ROUTE = "REOPTIMIZE_ROUTE"
    DELAY_ALERT = "DELAY_ALERT"
    PRIORITY_ESCALATION = "PRIORITY_ESCALATION"
    FLEET_REALLOCATION = "FLEET_REALLOCATION"


class RecommendationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AIRecommendation(Base):
    """Stores AI-generated decision support recommendations with full explainability."""
    __tablename__ = "ai_recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    recommendation_type = Column(Enum(RecommendationType), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # "order", "route", "driver", "vehicle"
    entity_id = Column(String(50), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0.0)
    recommendation = Column(Text, nullable=False)
    reasons = Column(JSON, nullable=True)  # List of explainability reasons
    factors = Column(JSON, nullable=True)  # Quantitative factor breakdown
    model_name = Column(String(100), nullable=False, default="logistics-ai-ensemble")
    model_version = Column(String(20), nullable=False, default="1.0.0")
    status = Column(Enum(RecommendationStatus), nullable=False, default=RecommendationStatus.PENDING, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String(36), nullable=True)
