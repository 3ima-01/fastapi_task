from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy import Enum as saEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.users.enums import UserStatusEnum
from src.utils.utils import utc_now

if TYPE_CHECKING:
    from src.transactions.models.transaction import Transaction
    from src.users.models.user_balance import UserBalance


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    status: Mapped[UserStatusEnum] = mapped_column(
        saEnum(UserStatusEnum, name="user_status_enum"),
        default=UserStatusEnum.ACTIVE,
    )
    created: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user_balance: Mapped[list["UserBalance"]] = relationship(
        "UserBalance",
        back_populates="owner",
        order_by="desc(UserBalance.amount)",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        order_by="desc(Transaction.created)",
    )
