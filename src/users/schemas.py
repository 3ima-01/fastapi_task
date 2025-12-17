from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, model_validator

from python_models import CurrencyEnum
from src.users.enums import UserStatusEnum


class RequestUserModel(BaseModel):
    email: EmailStr


class RequestUserUpdateModel(BaseModel):
    status: UserStatusEnum


class ResponseUserBalanceModel(BaseModel):
    currency: Optional[CurrencyEnum] = None
    amount: Optional[float] = None


class ResponseUserModel(BaseModel):
    id: Optional[int]
    email: Optional[EmailStr] = None
    status: Optional[UserStatusEnum] = None
    created: Optional[datetime] = None
    balances: Optional[List[ResponseUserBalanceModel]] = None


class UserModel(BaseModel):
    id: Optional[int]
    email: Optional[EmailStr] = None
    status: Optional[UserStatusEnum] = None
    created: Optional[datetime] = None


class UserBalanceModel(BaseModel):
    id: Optional[int]
    user_id: Optional[int] = None
    currency: Optional[CurrencyEnum] = None
    amount: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def validate_not_negative(cls, data: dict[str, Any]):
        amount = data.get("amount")
        if amount is not None and amount < 0:
            raise ValueError("Amount cannot be negative")

        return data
