from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.database.models import ExperimentStatus

class VariantSchema(BaseModel):
    name: str
    weight: int = Field(..., ge=0, le=100)
    value: Any
    is_control: bool = False

class ExperimentBase(BaseModel):
    flag_id: UUID
    name: str
    description: Optional[str] = None
    audience_share: float = Field(1.0, ge=0.0, le=1.0)
    targeting_rules: Optional[Dict[str, Any]] = None
    variants: List[VariantSchema]

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    audience_share: Optional[float] = Field(None, ge=0.0, le=1.0)
    targeting_rules: Optional[Dict[str, Any]] = None
    variants: Optional[List[VariantSchema]] = None

class ExperimentResponse(ExperimentBase):
    id: UUID
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)