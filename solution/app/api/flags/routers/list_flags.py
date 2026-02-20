from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database.session import get_session
from app.database.models import Flag, UserRole
from app.api.flags.schemas import FlagResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Flags"])

@router.get("/", response_model=List[FlagResponse])
async def list_flags(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN, UserRole.EXPERIMENTER]))
):
    result = await session.execute(select(Flag))
    return result.scalars().all()