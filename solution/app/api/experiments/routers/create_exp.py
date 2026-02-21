from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_session
from app.database.models import Experiment, Flag, UserRole, ExperimentStatus
from app.api.experiments.schemas import ExperimentCreate, ExperimentResponse
from app.utils.token_manager import check_permissions
from app.utils.validators import validate_experiment_logic

router = APIRouter(tags=["Experiments"])

@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    flag = await session.get(Flag, data.flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    variants_raw = [v.model_dump() for v in data.variants]
    validate_experiment_logic(variants_raw, data.audience_share)

    new_exp = Experiment(
        flag_id=data.flag_id,
        name=data.name,
        description=data.description,
        audience_share=data.audience_share,
        targeting_rules=data.targeting_rules,
        variants=variants_raw,
        status=ExperimentStatus.DRAFT
    )

    session.add(new_exp)
    await session.commit()
    await session.refresh(new_exp)
    return new_exp