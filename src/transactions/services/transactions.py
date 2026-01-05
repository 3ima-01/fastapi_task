from decimal import Decimal
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.transactions.enums import TransactionStatusEnum
from src.transactions.exceptions import (
    NotEnoughBalanceException,
    TransactionAlreadyRollbackedException,
    TransactionDoesNotBelongToUserException,
    TransactionNotExistsException,
)
from src.transactions.models import Transaction
from src.transactions.schemas import RequestTransactionModel, TransactionModel
from src.users.exceptions import UserBalanceDoesNotExists
from src.users.models import UserBalance
from src.users.services.users import UsersService
from src.utils.utils import utc_now


class TransactionsService:
    def __init__(self) -> None:
        self.users_service = UsersService()

    async def get_user_transactions(
        self,
        session: AsyncSession,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TransactionModel]:
        query = select(Transaction).order_by(desc(Transaction.created)).offset(skip).limit(limit)
        if user_id:
            query = query.where(Transaction.user_id == user_id)
        result = await session.execute(query)
        return [TransactionModel.model_validate(transaction) for transaction in result.scalars().all()]

    async def create_user_transaction(
        self,
        session: AsyncSession,
        transaction: RequestTransactionModel,
        user_id: int,
    ) -> TransactionModel:
        async with session.begin():
            user = await self.users_service.get_active_user(session, user_id)

            balance = await session.scalar(
                select(UserBalance)
                .where(
                    UserBalance.user_id == user.id,
                    UserBalance.currency == transaction.currency,
                )
                .with_for_update()
            )

            if not balance:
                raise UserBalanceDoesNotExists(user_id)

            new_amount = balance.amount + Decimal(str(transaction.amount))
            if new_amount < 0:
                raise NotEnoughBalanceException()
            balance.amount = new_amount

            new_transaction = Transaction(
                user_id=user_id,
                currency=transaction.currency,
                amount=transaction.amount,
                status=TransactionStatusEnum.PROCESSED,
                created=utc_now(),
            )
            session.add(new_transaction)

            await session.flush()
            return TransactionModel.model_validate(new_transaction)

    async def rollback(
        self,
        session: AsyncSession,
        user_id: int,
        transaction_id: int,
    ) -> TransactionModel:
        user = await self.users_service.get_active_user(session, user_id)

        result = await session.execute(
            select(Transaction, UserBalance)
            .join(UserBalance, (UserBalance.user_id == user.id) & (UserBalance.currency == Transaction.currency))
            .where((Transaction.user_id == user.id) & (Transaction.id == transaction_id))
            .with_for_update(of=(Transaction, UserBalance))
        )

        row = result.first()
        if not row:
            transaction_exists = await session.get(Transaction, transaction_id)
            if not transaction_exists:
                raise TransactionNotExistsException(transaction_id)
            raise TransactionDoesNotBelongToUserException(transaction_id, user_id)

        transaction, balance = row

        if transaction.status == TransactionStatusEnum.ROLL_BACKED:
            raise TransactionAlreadyRollbackedException(transaction_id)

        current_amount = float(balance.amount)
        transaction_amount = float(transaction.amount)

        if transaction.amount < 0:
            new_amount = current_amount + abs(transaction_amount)
        else:
            new_amount = current_amount - transaction_amount

        balance.amount = new_amount
        transaction.status = TransactionStatusEnum.ROLL_BACKED

        await session.commit()
        await session.refresh(transaction)

        return TransactionModel.model_validate(transaction)
