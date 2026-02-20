from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_session
from app.database.models import User, UserRole
from app.utils.token_manager import check_permissions
from app.api.users.schemas import UserResponse

router = APIRouter(tags=["Users"])

@router.get("/", response_model=list[UserResponse])
async def list_users(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN]))
):
    result = await session.execute(select(User))
    return result.scalars().all()