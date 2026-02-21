from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Dict, Any

class DecideRequest(BaseModel):
    subject_id: UUID
    keys: List[str]
    attributes: Dict[str, Any] = Field(default_factory=dict)

class FlagDecision(BaseModel):
    key: str
    value: Any
    decision_id: str
    metadata: Dict[str, Any]

class DecideResponse(BaseModel):
    results: List[FlagDecision]