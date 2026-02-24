from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_session
from app.database.models import Guardrail, UserRole, Experiment
from app.api.guardrails.schemas import GuardrailResponse, GuardrailCreate
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Guardrail"])

@router.post("/", response_model=GuardrailResponse, status_code=status.HTTP_201_CREATED)
async def create_guardrail_endpoint(
    data: GuardrailCreate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    exp = await session.get(Experiment, data.experiment_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Эксперимент не найден"}
        )
        
    new_gr = Guardrail(**data.model_dump())
    session.add(new_gr)
    await session.commit()
    await session.refresh(new_gr)
    return new_gr