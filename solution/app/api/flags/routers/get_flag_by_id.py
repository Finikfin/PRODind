from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.database.models import Flag, UserRole
from app.api.flags.schemas import FlagResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Flags"])

@router.get("/{flag_id}", response_model=FlagResponse)
async def get_flag_by_id(
    flag_id: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    flag = await session.get(Flag, flag_id)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Флаг не найден"}
        )
    return flag