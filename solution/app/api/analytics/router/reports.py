from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.database.session import get_session
from app.services.stats_service import StatsService
from app.utils.token_manager import check_permissions
from app.database.models import UserRole, Experiment

router = APIRouter(prefix="/experiment-results", tags=["Analytics"])

@router.get("/{experiment_id}")
async def get_experiment_report(
    experiment_id: UUID,
    goal_type: str = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    exp = await session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    stats = await StatsService.get_experiment_stats(
        session, 
        experiment_id, 
        goal_type,
        start_date,
        end_date
    )
    
    return {
        "experiment_id": experiment_id,
        "experiment_name": exp.name,
        "goal_type": goal_type,
        "results": stats
    }