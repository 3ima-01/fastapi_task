from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from src.users.enums import CurrencyEnum, UserStatusEnum


class RequestUserModel(BaseModel):
    email: EmailStr


class RequestUserUpdateModel(BaseModel):
    status: UserStatusEnum


class ResponseUserBalanceModel(BaseModel):
    currency: CurrencyEnum
    amount: float

    model_config = ConfigDict(from_attributes=True)


class ResponseUserModel(BaseModel):
    id: int
    email: EmailStr
    status: UserStatusEnum
    created: datetime
    balances: list[ResponseUserBalanceModel]

    model_config = ConfigDict(from_attributes=True)


class UserModel(BaseModel):
    id: int
    email: EmailStr
    status: UserStatusEnum
    created: datetime


class UserBalanceModel(BaseModel):
    id: int
    user_id: int
    currency: CurrencyEnum
    amount: float

    @model_validator(mode="before")
    @classmethod
    def validate_not_negative(cls, data: dict[str, Any]) -> dict[str, Any]:
        amount = data.get("amount")
        if amount is not None and amount < 0:
            raise ValueError("Amount cannot be negative")

        return data
