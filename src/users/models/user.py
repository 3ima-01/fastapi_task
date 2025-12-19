from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.users.enums import UserStatusEnum

if TYPE_CHECKING:
    from src.users.models.user_balance import UserBalance


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default=UserStatusEnum.ACTIVE)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

    user_balance: Mapped[list["UserBalance"]] = relationship(
        "UserBalance",
        back_populates="owner",
        order_by="desc(UserBalance.amount)",
    )
