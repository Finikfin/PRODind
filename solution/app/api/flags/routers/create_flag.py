from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_session
from app.database.models import Flag, UserRole
from app.api.flags.schemas import FlagCreate, FlagResponse
from app.utils.token_manager import check_permissions

router = APIRouter(tags=["Flags"])

@router.post("/", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
async def create_flag(
    data: FlagCreate, 
    session: AsyncSession = Depends(get_session),
    current_user = Depends(check_permissions([UserRole.ADMIN]))
):
    stmt = select(Flag).where(Flag.key == data.key)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Flag with key '{data.key}' already exists"
        )

    new_flag = Flag(**data.model_dump())
    session.add(new_flag)
    await session.commit()
    await session.refresh(new_flag)
    return new_flag