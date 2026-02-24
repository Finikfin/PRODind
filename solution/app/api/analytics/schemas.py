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

class VariantReport(BaseModel):
    variant: str
    total_users: int
    conversions: int
    conversion_rate: float

class ExperimentReportResponse(BaseModel):
    experiment_id: UUID
    experiment_name: str
    goal_type: str
    results: List[VariantReport]