from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_session
from app.database.models import Guardrail, UserRole
from app.api.guardrails.schemas import GuardrailUpdate, GuardrailResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Guardrail"])

@router.patch("/{guardrail_id}", response_model=GuardrailResponse)
async def update_guardrail_endpoint(
    guardrail_id: UUID,
    data: GuardrailUpdate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    gr = await session.get(Guardrail, guardrail_id)
    if not gr:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(gr, key, value)
    
    await session.commit()
    await session.refresh(gr)
    return gr