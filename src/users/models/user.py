from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from src.database import Base


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=True, unique=True)
    status = Column(String, nullable=True)
    created = Column(DateTime, nullable=True)

    user_balance = relationship("UserBalance", back_populates="owner")
