from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from uuid import UUID

class DecisionMetadata(BaseModel):
    experiment_id: Optional[UUID] = None
    variant_name: Optional[str] = None
    reason: str 

class FlagDecision(BaseModel):
    key: str
    value: Any
    is_default: bool
    decision_id: Optional[str] = None
    metadata: DecisionMetadata

class DecideRequest(BaseModel):
    subject_id: UUID
    keys: List[str]
    attributes: Dict[str, Any] = Field(default_factory=dict)

class DecideResponse(BaseModel):
    results: List[FlagDecision]