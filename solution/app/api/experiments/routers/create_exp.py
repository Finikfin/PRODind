from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_session
from app.database.models import Experiment, Flag, UserRole, ExperimentStatus
from app.api.experiments.schemas import ExperimentCreate, ExperimentResponse
from app.utils.token_manager import check_permissions
from app.utils.validators import validate_experiment_logic, validate_domain_conflict

router = APIRouter(tags=["Experiments"])

@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    flag = await session.get(Flag, data.flag_id)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Флаг не найден"}
        )

    variants_raw = [v.model_dump() for v in data.variants]
    
    validate_experiment_logic(variants_raw, data.audience_share, flag_type=flag.type)

    if data.conflict_domain_id:
        await validate_domain_conflict(
            session=session,
            domain_id=data.conflict_domain_id,
            new_offset=data.domain_offset,
            new_share_pct=data.audience_share
        )

    new_exp = Experiment(
        flag_id=data.flag_id,
        creator_id=current_user.id,
        name=data.name,
        description=data.description,
        audience_share=data.audience_share,
        conflict_domain_id=data.conflict_domain_id,
        domain_offset=data.domain_offset,
        targeting_rules=data.targeting_rules,
        variants=variants_raw,
        status=ExperimentStatus.DRAFT,
        conclusion=None
    )

    session.add(new_exp)
    await session.commit()
    await session.refresh(new_exp)
    return new_exp