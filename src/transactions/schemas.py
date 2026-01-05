from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.exceptions import BadRequestDataException
from src.transactions.enums import TransactionStatusEnum
from src.users.enums import CurrencyEnum


class RequestTransactionModel(BaseModel):
    currency: CurrencyEnum
    amount: Decimal = Field(max_digits=12, decimal_places=2)

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise BadRequestDataException(detail="Transaction can not have zero amount")
        return v


class TransactionModel(BaseModel):
    id: int
    user_id: int
    currency: CurrencyEnum
    amount: float
    status: TransactionStatusEnum
    created: datetime

    model_config = ConfigDict(from_attributes=True)
