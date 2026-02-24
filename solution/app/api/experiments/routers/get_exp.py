from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List
from app.database.session import get_session
from app.database.models import Experiment, UserRole
from app.api.experiments.schemas import ExperimentResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Experiments"])

@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    result = await session.execute(select(Experiment))
    return result.scalars().all()

@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    exp = await session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"message": "Эксперимент не найден"}
        )
    return exp