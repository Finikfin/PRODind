from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List
from app.database.session import get_session
from app.database.models import Guardrail, UserRole
from app.api.guardrails.schemas import GuardrailResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Guardrail"])

@router.get("/experiment/{experiment_id}", response_model=List[GuardrailResponse])
async def list_guardrails_endpoint(
    experiment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    result = await session.execute(
        select(Guardrail).where(Guardrail.experiment_id == experiment_id)
    )
    return result.scalars().all()