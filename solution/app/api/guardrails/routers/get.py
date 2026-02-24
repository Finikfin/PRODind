from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database.session import get_session
from app.database.models import Guardrail, UserRole
from app.api.guardrails.schemas import GuardrailResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Guardrail"])

@router.get("/{guardrail_id}", response_model=GuardrailResponse)
async def get_guardrail_endpoint(
    guardrail_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER, UserRole.APPROVER]))
):
    gr = await session.get(Guardrail, guardrail_id)
    
    if not gr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Guardrail not found"
        )
        
    return gr