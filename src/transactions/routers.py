from datetime import datetime, timedelta
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from queries import (
    get_not_rollbacked_deposit_amount,
    get_not_rollbacked_transactions_count,
    get_not_rollbacked_withdraw_amount,
    get_registered_and_deposit_users_count,
    get_registered_and_not_rollbacked_deposit_users_count,
    get_registered_users_count,
    get_transactions_count,
)
from src.database import get_async_session
from src.transactions.schemas import RequestTransactionModel, TransactionModel
from src.transactions.services.transactions import TransactionsService
from src.utils.dependencies import validate_positive_id

router = APIRouter(prefix="", tags=["Transactions"])


@router.get(
    "/transactions",
    response_model=Optional[list[TransactionModel]],
    status_code=status.HTTP_200_OK,
)
async def get_transactions(
    user_id: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session),
) -> Sequence[TransactionModel]:
    return await TransactionsService().get_user_transactions(
        session=session,
        user_id=user_id,
    )


@router.post(
    "/{user_id}/transactions",
    response_model=Optional[TransactionModel],
    status_code=status.HTTP_200_OK,
)
async def post_transaction(
    transaction: RequestTransactionModel,
    user_id: int = Depends(validate_positive_id),
    session: AsyncSession = Depends(get_async_session),
):
    return await TransactionsService().create_user_transaction(
        session=session,
        transaction=transaction,
        user_id=user_id,
    )


@router.patch(
    "/{user_id}/transactions/{transaction_id}",
    response_model=Optional[TransactionModel],
    status_code=status.HTTP_200_OK,
)
async def patch_rollback_transaction(
    user_id: int,
    transaction_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    return await TransactionsService().rollback(
        session=session,
        transaction_id=transaction_id,
        user_id=user_id,
    )


@router.get("/transactions/analysis", response_model=Optional[list] | None, status_code=status.HTTP_200_OK)
async def get_transaction_analysis(session: AsyncSession = Depends(get_async_session)) -> list[dict]:
    dt_gt = datetime.utcnow().date() - timedelta(weeks=1) + timedelta(days=1)
    dt_lt = datetime.utcnow().date()
    results = []
    for i in range(52):
        registered_users_count = await get_registered_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        registered_and_deposit_users_count = await get_registered_and_deposit_users_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        )
        registered_and_not_rollbacked_deposit_users_count = await get_registered_and_not_rollbacked_deposit_users_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        )
        not_rollbacked_deposit_amount = await get_not_rollbacked_deposit_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_withdraw_amount = await get_not_rollbacked_withdraw_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        transactions_count = await get_transactions_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_transactions_count = await get_not_rollbacked_transactions_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        )
        result = {
            "start_date": dt_gt,
            "end_date": dt_lt,
            "registered_users_count": registered_users_count,
            "registered_and_deposit_users_count": registered_and_deposit_users_count,
            "registered_and_not_rollbacked_deposit_users_count": registered_and_not_rollbacked_deposit_users_count,
            "not_rollbacked_deposit_amount": not_rollbacked_deposit_amount,
            "not_rollbacked_withdraw_amount": not_rollbacked_withdraw_amount,
            "transactions_count": transactions_count,
            "not_rollbacked_transactions_count": not_rollbacked_transactions_count,
        }
        for field in (
            "registered_users_count",
            "registered_and_deposit_users_count",
            "registered_and_not_rollbacked_deposit_users_count",
            "not_rollbacked_deposit_amount",
            "not_rollbacked_withdraw_amount",
            "transactions_count",
            "not_rollbacked_transactions_count",
        ):
            if result[field] > 0:
                results.append(result)
                break
        dt_gt -= timedelta(weeks=1)
        dt_lt -= timedelta(weeks=1)
    return results
