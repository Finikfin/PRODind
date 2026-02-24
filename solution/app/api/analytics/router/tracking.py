from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

from app.database.session import get_session
from app.database.models import Conversion, Exposure
from app.api.analytics.schemas import TrackRequest
from app.services.guardrail_service import GuardrailService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("/track", status_code=status.HTTP_201_CREATED)
async def track_event(
    data: TrackRequest,
    session: AsyncSession = Depends(get_session)
):
    exposure_res = await session.execute(
        select(Exposure).where(Exposure.decision_id == data.decision_id)
    )
    exposure = exposure_res.scalar_one_or_none()

    if not exposure:
        raise HTTPException(400, "Invalid decision_id")

    stmt = insert(Conversion).values(
        event_id=data.event_id,
        subject_id=data.subject_id,
        goal_type=data.goal_type,
        decision_id=data.decision_id,
        timestamp=datetime.utcnow()
    ).on_conflict_do_nothing(index_elements=['event_id'])
    
    await session.execute(stmt)
    await session.flush()

    await GuardrailService.check_and_trigger(session, exposure.experiment_id)
    await session.commit()
    
    return {"status": "success"}