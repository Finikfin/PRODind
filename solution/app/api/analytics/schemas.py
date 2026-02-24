from pydantic import BaseModel, Field
from uuid import UUID
from typing import Dict, Any, Optional

class TrackRequest(BaseModel):
    subject_id: UUID
    goal_type: str = Field(..., example="purchase_completed")
    decision_id: str
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)