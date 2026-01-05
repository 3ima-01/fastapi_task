from typing import Any, Optional, Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.services.analytics import AnalyticsService
from src.database import get_async_session
from src.transactions.schemas import RequestTransactionModel, TransactionModel
from src.transactions.services.transactions import TransactionsService
from src.utils.dependencies import validate_positive_id


router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
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
    "/{user_id}",
    response_model=Optional[TransactionModel],
    status_code=status.HTTP_200_OK,
)
async def post_transaction(
    transaction: RequestTransactionModel,
    user_id: int = Depends(validate_positive_id),
    session: AsyncSession = Depends(get_async_session),
) -> TransactionModel:
    return await TransactionsService().create_user_transaction(
        session=session,
        transaction=transaction,
        user_id=user_id,
    )


@router.patch(
    "/{transaction_id}/user/{user_id}/rollback",
    response_model=Optional[TransactionModel],
    status_code=status.HTTP_200_OK,
)
async def patch_rollback_transaction(
    user_id: int,
    transaction_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> TransactionModel:
    return await TransactionsService().rollback(
        session=session,
        transaction_id=transaction_id,
        user_id=user_id,
    )


@router.get("/analysis", response_model=Optional[list[dict[str, Any]]] | None, status_code=status.HTTP_200_OK)
async def get_transaction_analysis(session: AsyncSession = Depends(get_async_session)) -> list[dict[str, Any]]:
    return await AnalyticsService().generate_weekly_reports(session)
