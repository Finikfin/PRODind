from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from uuid import UUID
from typing import Optional
from datetime import datetime

from app.database.session import get_session
from app.database.models import Conversion, Exposure, Experiment, UserRole
from app.api.analytics.schemas import TrackRequest
from app.services.stats_service import StatsService
from app.services.guardrail_service import GuardrailService
from app.utils.token_manager import check_permissions
from sqlalchemy import select

router = APIRouter(tags=["Analytics"])

@router.post("/track", status_code=status.HTTP_201_CREATED)
async def track_event(data: TrackRequest, session: AsyncSession = Depends(get_session)):

    exposure = (await session.execute(select(Exposure).where(Exposure.decision_id == data.decision_id))).scalar_one_or_none()
    if not exposure:
        raise HTTPException(400, "Invalid decision_id")

    stmt = insert(Conversion).values(
        event_id=str(data.event_id), subject_id=data.subject_id,
        goal_type=data.goal_type, decision_id=data.decision_id, timestamp=datetime.utcnow()
    ).on_conflict_do_nothing(index_elements=['event_id'])
    
    await session.execute(stmt)
    await session.flush()

    await GuardrailService.check_and_trigger(session, exposure.experiment_id)
    await session.commit()
    return {"status": "success"}

@router.get("/experiment-results/{experiment_id}")
async def get_report(
    experiment_id: UUID, goal_type: str = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    stats = await StatsService.get_experiment_stats(session, experiment_id, goal_type, start_date, end_date)
    return {"experiment_id": experiment_id, "results": stats}