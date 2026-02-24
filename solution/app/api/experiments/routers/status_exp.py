from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from app.database.session import get_session
from app.database.models import Experiment, ExperimentStatus, UserRole, ExperimentApproval, User
from app.api.experiments.schemas import ExperimentResponse
from app.utils.token_manager import check_permissions
from app.utils.validators import validate_domain_conflict

router = APIRouter(tags=["Experiments"])

class StatusUpdate(BaseModel):
    status: ExperimentStatus
    conclusion: Optional[str] = None

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
        .options(joinedload(Experiment.creator).joinedload(User.allowed_approvers))
    )
    result = await session.execute(stmt)
    exp = result.scalar_one_or_none()

    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    new_status = update_data.status

    if new_status == ExperimentStatus.APPROVED:
        if current_user.role not in [UserRole.ADMIN, UserRole.APPROVER]:
            raise HTTPException(status_code=403, detail="Forbidden role")
        
        if current_user.role != UserRole.ADMIN and exp.creator.allowed_approvers:
            allowed_ids = [u.id for u in exp.creator.allowed_approvers]
            if current_user.id not in allowed_ids:
                raise HTTPException(status_code=403, detail="Not in allowed approvers list for this creator")

        existing_vote = await session.execute(
            select(ExperimentApproval).where(
                and_(ExperimentApproval.experiment_id == experiment_id, ExperimentApproval.approver_id == current_user.id)
            )
        )
        if existing_vote.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Already approved")

        session.add(ExperimentApproval(experiment_id=experiment_id, approver_id=current_user.id))
        await session.flush()

        votes_count = await session.scalar(
            select(func.count(ExperimentApproval.id)).where(ExperimentApproval.experiment_id == experiment_id)
        )

        threshold = exp.creator.min_approvals_required
        if votes_count < threshold:
            await session.commit()
            return exp

    if new_status == ExperimentStatus.RUNNING:
        if exp.status not in [ExperimentStatus.APPROVED, ExperimentStatus.PAUSED]:
            raise HTTPException(status_code=400, detail="Must be APPROVED or PAUSED")

        active_check = await session.execute(
            select(Experiment).where(
                and_(Experiment.flag_id == exp.flag_id, Experiment.status == ExperimentStatus.RUNNING, Experiment.id != experiment_id)
            )
        )
        if active_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Another experiment is running for this flag")

        if exp.conflict_domain_id:
            await validate_domain_conflict(
                session=session,
                domain_id=exp.conflict_domain_id,
                new_offset=exp.domain_offset,
                new_share_pct=exp.audience_share,
                exclude_id=exp.id
            )

    if new_status == ExperimentStatus.FINISHED:
        if not update_data.conclusion:
            raise HTTPException(status_code=400, detail="Conclusion required")
        exp.conclusion = update_data.conclusion

    exp.status = new_status
    await session.commit()
    await session.refresh(exp)
    return exp