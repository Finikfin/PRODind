from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.database.models import GuardrailAction

class GuardrailBase(BaseModel):
    metric_key: str
    threshold: float
    operator: str = Field(">", pattern="^(>|<|>=|<=|==)$")
    action: GuardrailAction = GuardrailAction.PAUSE

class GuardrailCreate(GuardrailBase):
    experiment_id: UUID

class GuardrailUpdate(BaseModel):
    metric_key: Optional[str] = None
    threshold: Optional[float] = None
    operator: Optional[str] = None
    action: Optional[GuardrailAction] = None

class GuardrailResponse(GuardrailBase):
    id: UUID
    experiment_id: UUID
    is_triggered: bool
    triggered_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)