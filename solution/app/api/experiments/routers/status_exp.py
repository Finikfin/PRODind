from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from uuid import UUID
from datetime import datetime

from app.database.session import get_session
from app.database.models import Experiment, ExperimentStatus, UserRole, ExperimentApproval, User
from app.api.experiments.schemas import ExperimentResponse, StatusUpdate
from app.utils.token_manager import check_permissions
from app.utils.validators import validate_domain_conflict

router = APIRouter(tags=["Experiments"])

@router.patch("/{experiment_id}/status", response_model=ExperimentResponse)
async def change_experiment_status(
    experiment_id: UUID,
    update_data: StatusUpdate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    stmt = (
        select(Experiment)
        .where(Experiment.id == experiment_id)
        .options(
            joinedload(Experiment.creator),
            joinedload(Experiment.guardrails),
            joinedload(Experiment.approvals)
        )
    )
    result = await session.execute(stmt)
    exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    new_status = update_data.status

    if new_status == ExperimentStatus.APPROVED:
        if current_user.role not in [UserRole.ADMIN, UserRole.APPROVER]:
            raise HTTPException(status_code=403, detail="Forbidden role")
        
        existing_vote = await session.execute(
            select(ExperimentApproval).where(
                and_(ExperimentApproval.experiment_id == experiment_id, ExperimentApproval.approver_id == current_user.id)
            )
        )
        if not existing_vote.scalar_one_or_none():
            session.add(ExperimentApproval(experiment_id=experiment_id, approver_id=current_user.id))
            await session.flush()

        votes_count = await session.scalar(
            select(func.count(ExperimentApproval.id)).where(ExperimentApproval.experiment_id == experiment_id)
        )

        if votes_count >= exp.creator.min_approvals_required:
            exp.status = ExperimentStatus.APPROVED
    
    elif new_status == ExperimentStatus.RUNNING:
        if exp.status not in [ExperimentStatus.APPROVED, ExperimentStatus.PAUSED]:
            raise HTTPException(status_code=400, detail="Must be APPROVED or PAUSED")
        
        if not exp.started_at:
            exp.started_at = datetime.utcnow()
        exp.status = ExperimentStatus.RUNNING

    elif new_status == ExperimentStatus.FINISHED:
        if not update_data.conclusion:
            raise HTTPException(status_code=400, detail="Conclusion required")
        exp.status = ExperimentStatus.FINISHED
        exp.outcome = update_data.outcome
        exp.conclusion = update_data.conclusion
        exp.finished_at = datetime.utcnow()
    
    else:
        exp.status = new_status

    await session.commit()
    await session.refresh(exp)
    
    exp.current_approvals = len(exp.approvals)
    exp.required_approvals = exp.creator.min_approvals_required
    
    return exp