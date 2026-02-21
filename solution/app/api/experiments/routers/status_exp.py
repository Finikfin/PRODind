from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database.session import get_session
from app.database.models import Experiment, ExperimentStatus, UserRole
from app.api.experiments.schemas import ExperimentResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Experiments"])

@router.patch("/{experiment_id}/status", response_model=ExperimentResponse)
async def change_experiment_status(
    experiment_id: UUID,
    new_status: ExperimentStatus,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    exp = await session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if new_status == ExperimentStatus.APPROVED:
        if current_user.role not in [UserRole.ADMIN, UserRole.APPROVER]:
            raise HTTPException(status_code=403, detail="Only Approver can approve experiments")

    if new_status == ExperimentStatus.RUNNING:
        if exp.status != ExperimentStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Experiment must be APPROVED to start")
        
        active_check = await session.execute(
            select(Experiment).where(
                Experiment.flag_id == exp.flag_id,
                Experiment.status == ExperimentStatus.RUNNING,
                Experiment.id != experiment_id
            )
        )
        if active_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Another experiment is already running for this flag")

    exp.status = new_status
    await session.commit()
    await session.refresh(exp)
    return exp