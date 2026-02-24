from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.database.models import Experiment, ExperimentApproval, ExperimentStatus, User, UserRole

class ReviewService:
    @staticmethod
    async def approve(session, experiment_id, approver: User):
        stmt = (
            select(Experiment)
            .options(selectinload(Experiment.creator))
            .where(Experiment.id == experiment_id)
        )
        res = await session.execute(stmt)
        exp = res.scalar_one_or_none()

        if not exp:
            raise HTTPException(404, "Experiment not found")
        if exp.status != ExperimentStatus.ON_REVIEW:
            raise HTTPException(400, "Only experiments ON_REVIEW can be approved")
        if approver.role not in [UserRole.APPROVER, UserRole.ADMIN]:
            raise HTTPException(403, "Insufficient permissions")
        if exp.creator_id == approver.id:
            raise HTTPException(400, "Cannot approve your own experiment")

        try:
            new_approval = ExperimentApproval(experiment_id=experiment_id, approver_id=approver.id)
            session.add(new_approval)
            await session.flush()
        except IntegrityError:
            raise HTTPException(400, "Already approved by this user")

        count_stmt = select(func.count()).where(ExperimentApproval.experiment_id == experiment_id)
        current_approvals = await session.scalar(count_stmt)

        if current_approvals >= exp.creator.min_approvals_required:
            exp.status = ExperimentStatus.APPROVED
        
        await session.commit()