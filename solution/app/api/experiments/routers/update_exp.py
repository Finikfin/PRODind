from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_session
from app.database.models import Experiment, ExperimentStatus, UserRole
from app.api.experiments.schemas import ExperimentUpdate, ExperimentResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Experiments"])

@router.patch("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: UUID,
    experiment_data: ExperimentUpdate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    exp = await session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if exp.status == ExperimentStatus.RUNNING:
        raise HTTPException(
            status_code=400, 
            detail="Cannot edit parameters of a RUNNING experiment. Pause or finish it first."
        )

    update_data = experiment_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exp, key, value)

    await session.commit()
    await session.refresh(exp)
    
    return exp