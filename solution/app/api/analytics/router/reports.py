from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_session
from app.services.stats_service import StatsService
from app.utils.token_manager import check_permissions
from app.database.models import UserRole

router = APIRouter()

@router.get("/experiment-results/{experiment_id}")
async def get_experiment_report(
    experiment_id: UUID,
    goal_type: str = Query(..., description="Тип цели для анализа, например 'purchase'"),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    stats = await StatsService.get_experiment_stats(session, experiment_id, goal_type)
    return {
        "experiment_id": experiment_id,
        "goal_type": goal_type,
        "results": stats
    }