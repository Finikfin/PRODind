from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_session
from app.database.models import User, UserRole
from app.utils.token_manager import check_permissions

router = APIRouter(prefix="/users", tags=["Users Admin"])

@router.patch("/{user_id}/threshold")
async def set_approval_threshold(
    user_id: UUID, 
    min_approvals: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN]))
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.min_approvals_required = min_approvals
    await session.commit()
    return {"status": "ok", "user_id": user_id, "new_threshold": min_approvals}