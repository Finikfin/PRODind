from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_session
from app.database.models import Guardrail, UserRole
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Guardrail"])

@router.delete("/{guardrail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guardrail_endpoint(
    guardrail_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN]))
):
    gr = await session.get(Guardrail, guardrail_id)
    if not gr:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    await session.delete(gr)
    await session.commit()