from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_session
from app.database.models import Experiment, ExperimentStatus, UserRole
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Experiments"])

@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN]))
):
    exp = await session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if exp.status == ExperimentStatus.DRAFT:
        await session.delete(exp)
    else:
        exp.status = ExperimentStatus.FINISHED
    
    await session.commit()
    return None