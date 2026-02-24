from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from uuid import UUID
from app.database.session import get_session
from app.database.models import User, UserRole, approver_experimenter_association
from app.utils.token_manager import check_permissions

router = APIRouter(prefix="/users", tags=["Users Admin"])

@router.post("/{experimenter_id}/approvers/{approver_id}")
async def assign_approver_to_experimenter(
    experimenter_id: UUID,
    approver_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN]))
):
    exp_user = await session.get(User, experimenter_id)
    app_user = await session.get(User, approver_id)
    
    if not exp_user or not app_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if app_user.role not in [UserRole.APPROVER, UserRole.ADMIN]:
        raise HTTPException(status_code=400, detail="Target user must be an APPROVER or ADMIN")

    stmt = insert(approver_experimenter_association).values(
        experimenter_id=experimenter_id, 
        approver_id=approver_id
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success"}