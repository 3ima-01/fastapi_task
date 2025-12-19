from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.users.dependencies import validate_positive_user_id
from src.users.schemas import RequestUserModel, RequestUserUpdateModel, ResponseUserModel, UserModel
from src.users.services.users import UsersService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/users",
    response_model=Optional[list[ResponseUserModel]] | None,
    status_code=status.HTTP_200_OK,
)
async def get_users(
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    user_status: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
) -> List[ResponseUserModel]:
    return await UsersService().get_users_with_relations(
        session,
        user_id=user_id,
        email=email,
        user_status=user_status,
    )


@router.post("/users", status_code=status.HTTP_200_OK)
async def post_user(user: RequestUserModel, session: AsyncSession = Depends(get_async_session)):
    return await UsersService().create_user_with_balance(session, user=user)


@router.patch("/users/{user_id}", response_model=Optional[UserModel] | None)
async def patch_user(
    update_data: RequestUserUpdateModel,
    user_id: int = Depends(validate_positive_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    return await UsersService().patch_user(
        session,
        user_id=user_id,
        update_data=update_data,
    )
