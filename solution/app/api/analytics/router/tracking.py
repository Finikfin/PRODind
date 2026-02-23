from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database.session import get_session
from app.database.models import Conversion
from app.api.analytics.schemas import TrackRequest

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("/track", status_code=status.HTTP_201_CREATED)
async def track_event(
    data: TrackRequest,
    session: AsyncSession = Depends(get_session)
):
    conversion = Conversion(
        subject_id=data.subject_id,
        goal_type=data.goal_type,
        properties=data.properties,
        timestamp=datetime.utcnow()
    )
    
    session.add(conversion)
    await session.commit()
    
    return {"status": "success", "recorded_at": conversion.timestamp}