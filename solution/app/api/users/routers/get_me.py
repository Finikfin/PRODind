from fastapi import APIRouter, Depends
from app.api.users.schemas import UserResponse
from app.utils.token_manager import get_current_user

router = APIRouter(tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """
    Возвращает данные текущего авторизованного пользователя.
    """
    return current_user