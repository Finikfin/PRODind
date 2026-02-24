from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime
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

    @staticmethod
    async def change_status(session, experiment_id, new_status: ExperimentStatus):
        exp = await session.get(Experiment, experiment_id)
        if not exp:
            raise HTTPException(404, "Experiment not found")

        if new_status == ExperimentStatus.RUNNING:
            if exp.status not in [ExperimentStatus.APPROVED, ExperimentStatus.PAUSED]:
                raise HTTPException(400, "Experiment must be APPROVED or PAUSED to start")
            
            check_running = await session.scalar(
                select(func.count(Experiment.id))
                .where(Experiment.flag_id == exp.flag_id)
                .where(Experiment.status == ExperimentStatus.RUNNING)
                .where(Experiment.id != experiment_id)
            )
            if check_running > 0:
                raise HTTPException(400, "Another experiment is already RUNNING for this flag")
            
            if not exp.started_at:
                exp.started_at = datetime.utcnow()
        
        if new_status in [ExperimentStatus.FINISHED, ExperimentStatus.ARCHIVED]:
            exp.finished_at = datetime.utcnow()

        exp.status = new_status
        await session.commit()
        return exp