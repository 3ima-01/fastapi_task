from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as saEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.transactions.enums import TransactionStatusEnum
from src.utils.utils import utc_now

if TYPE_CHECKING:
    from src.users.models.user import User


class Transaction(Base):
    __tablename__ = "transaction"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    status: Mapped[TransactionStatusEnum] = mapped_column(
        saEnum(TransactionStatusEnum, name="transaction_status_enum"), nullable=True, default=None
    )
    created: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=utc_now)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="transactions",
    )
