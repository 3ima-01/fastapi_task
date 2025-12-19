from datetime import datetime
from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.users.enums import CurrencyEnum, UserStatusEnum
from src.users.exceptions import (
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
    UserAlreadyExistsException,
    UserNotExistsException,
)
from src.users.models.user import User
from src.users.models.user_balance import UserBalance
from src.users.schemas import (
    RequestUserModel,
    RequestUserUpdateModel,
    ResponseUserModel,
    UserModel,
)


class UsersService:
    async def get_users_with_relations(
        self,
        session: AsyncSession,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        user_status: Optional[str] = None,
    ) -> list[ResponseUserModel]:
        """
        Retrieve users with their associated balance information.

        This method fetches user data along with their account balances. It supports
        filtering by various criteria. When multiple filters are provided, they are
        combined using AND logic.
        """
        q = select(User).options(selectinload(User.user_balance)).order_by(User.created.desc())
        if user_id is not None:
            q = q.where(User.id == user_id)
        if email is not None:
            q = q.where(User.email.ilike(email))
        if user_status is not None:
            q = q.where(User.status == user_status)

        result = await session.execute(q)
        users = result.scalars().all()

        response_users: list[ResponseUserModel] = []
        for user in users:
            response_users.append(
                ResponseUserModel(
                    id=user.id,
                    email=user.email,
                    status=UserStatusEnum(user.status),
                    created=user.created,
                    balances=user.user_balance,
                )
            )

        return response_users

    async def create_user_with_balance(
        self,
        session: AsyncSession,
        user: RequestUserModel,
    ):
        """
        Creates a new user with zero-initialized balances for all supported currencies.
        1. Checks if a user with the given email already exists.
        2. If not, inserts a new active user.
        3. Immediately creates initial balance records (amount = 0.0) for all currencies in `CurrencyEnum`.
        """
        async with session.begin():
            existing_user = await session.scalar(select(User.id).where(User.email == user.email))
            if existing_user:
                raise UserAlreadyExistsException(user.email)

            # --- user create ---
            now = datetime.now()
            db_user = User(email=user.email, status="ACTIVE", created=now)
            session.add(db_user)

            await session.flush()

            currencies = [c.value for c in CurrencyEnum]
            balance_data = [
                {"user_id": db_user.id, "currency": cur, "amount": 0.0, "created": now} for cur in currencies
            ]

            # bulk-insert
            await session.execute(
                insert(UserBalance),
                balance_data,
            )

            return UserModel(
                id=db_user.id,
                email=db_user.email,
                status=UserStatusEnum(db_user.status),
                created=db_user.created,
            )

    async def patch_user(
        self,
        session: AsyncSession,
        user_id: int,
        update_data: RequestUserUpdateModel,
    ):
        """
        Patch user status
        """
        async with session.begin():
            db_user = await session.scalar(select(User).where(User.id == user_id).with_for_update())

            if not db_user:
                raise UserNotExistsException(user_id)

            current_status = db_user.status
            new_status = update_data.status.value

            if current_status == new_status:
                if current_status == UserStatusEnum.BLOCKED:
                    raise UserAlreadyBlockedException(user_id)
                elif current_status == UserStatusEnum.ACTIVE:
                    raise UserAlreadyActiveException(user_id)

            db_user.status = new_status

            return UserModel(
                id=db_user.id,
                email=db_user.email,
                status=UserStatusEnum(db_user.status),
                created=db_user.created,
            )
