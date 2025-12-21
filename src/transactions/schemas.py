from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import status
from pydantic import BaseModel, field_validator

from exceptions import BadRequestDataException
from src.transactions.enums import TransactionStatusEnum
from src.users.enums import CurrencyEnum


class RequestTransactionModel(BaseModel):
    currency: CurrencyEnum
    amount: float

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise BadRequestDataException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transaction can not have zero amount",
            )
        return v


class TransactionModel(BaseModel):
    id: Optional[int]
    user_id: Optional[int] = None
    currency: Optional[CurrencyEnum] = None
    amount: Optional[float] = None
    status: Optional[TransactionStatusEnum] = None
    created: Optional[datetime] = None
