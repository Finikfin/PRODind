from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class TrackRequest(BaseModel):
    event_id: UUID 
    subject_id: UUID
    goal_type: str
    decision_id: str
    properties: Optional[dict] = None

class ReportVariant(BaseModel):
    variant_name: str
    is_control: bool
    exposures_count: int
    conversions_count: int
    conversion_rate: float

class ReportResponse(BaseModel):
    experiment_id: UUID
    goal_type: str
    variants: List[ReportVariant]