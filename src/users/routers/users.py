from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.users.enums import UserStatusEnum
from src.users.schemas import RequestUserModel, RequestUserUpdateModel, ResponseUserModel, UserModel
from src.users.services.users import UsersService
from src.utils.dependencies import validate_positive_id

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=Optional[list[ResponseUserModel]],
    status_code=status.HTTP_200_OK,
)
async def get_users(
    user_id: Optional[int] = None,
    email: Optional[EmailStr] = None,
    user_status: Optional[UserStatusEnum] = None,
    session: AsyncSession = Depends(get_async_session),
) -> list[ResponseUserModel]:
    return await UsersService().get_users_with_relations(session, user_id=user_id, email=email, user_status=user_status)


@router.post(
    "",
    response_model=UserModel,
    status_code=status.HTTP_200_OK,
)
async def post_user(user: RequestUserModel, session: AsyncSession = Depends(get_async_session)) -> UserModel:
    return await UsersService().create_user_with_balance(session, user=user)


@router.patch(
    "/{user_id}",
    response_model=Optional[UserModel],
    status_code=status.HTTP_200_OK,
)
async def patch_user(
    update_data: RequestUserUpdateModel,
    user_id: int = Depends(validate_positive_id),
    session: AsyncSession = Depends(get_async_session),
) -> Optional[UserModel]:
    return await UsersService().patch_user_status(session, user_id=user_id, update_data=update_data)
