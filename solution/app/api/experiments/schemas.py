from pydantic import BaseModel, Field, ConfigDict, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.database.models import ExperimentStatus, ExperimentOutcome, GuardrailAction

class VariantSchema(BaseModel):
    name: str
    weight: int = Field(..., ge=0, le=100)
    value: Any
    is_control: bool = False

class GuardrailSchema(BaseModel):
    id: UUID
    metric_key: str
    operator: str
    threshold: float
    action: GuardrailAction
    is_triggered: bool
    triggered_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class GuardrailCreate(BaseModel):
    metric_key: str
    operator: str = ">"
    threshold: float
    action: GuardrailAction = GuardrailAction.PAUSE

class ExperimentBase(BaseModel):
    flag_id: UUID
    name: str
    description: Optional[str] = None
    audience_share: float = Field(1.0, ge=0.0, le=1.0)
    conflict_domain_id: Optional[UUID] = None
    domain_offset: int = Field(0, ge=0, le=99)
    targeting_rules: Optional[Dict[str, Any]] = None
    variants: List[VariantSchema]

    @model_validator(mode='after')
    def validate_variants_logic(self) -> 'ExperimentBase':
        if not self.variants:
            raise ValueError("Experiment must have at least one variant")
        total_weight = sum(v.weight for v in self.variants)
        if total_weight != 100:
            raise ValueError(f"Total weight must be exactly 100, got {total_weight}")
        names = [v.name for v in self.variants]
        if len(names) != len(set(names)):
            raise ValueError("Variant names must be unique")
        return self

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    audience_share: Optional[float] = Field(None, ge=0.0, le=1.0)
    conflict_domain_id: Optional[UUID] = None
    domain_offset: Optional[int] = Field(None, ge=0, le=99)
    targeting_rules: Optional[Dict[str, Any]] = None
    variants: Optional[List[VariantSchema]] = None

class StatusUpdate(BaseModel):
    status: ExperimentStatus
    outcome: Optional[ExperimentOutcome] = None
    conclusion: Optional[str] = None

class ExperimentResponse(ExperimentBase):
    id: UUID
    status: ExperimentStatus
    outcome: Optional[ExperimentOutcome] = None
    conclusion: Optional[str] = None
    version: int
    creator_id: UUID
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    current_approvals: int = 0
    required_approvals: int = 1
    guardrails: List[GuardrailSchema] = []
    model_config = ConfigDict(from_attributes=True)