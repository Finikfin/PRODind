from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, Any
from datetime import datetime

class FlagCreate(BaseModel):
    key: str
    description: Optional[str] = None
    type: str = "boolean"
    default_value: dict 

class FlagResponse(BaseModel):
    id: UUID
    key: str
    description: Optional[str]
    type: str
    default_value: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)