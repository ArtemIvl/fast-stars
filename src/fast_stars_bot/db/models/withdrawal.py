import enum
from datetime import date

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import Base


class WithdrawalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stars = Column(Numeric(10, 2), nullable=False)
    ton_address = Column(String, nullable=True, default=None)
    status = Column(
        Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING, nullable=False
    )
    created_at = Column(Date, nullable=False, default=date.today)

    user = relationship("User", back_populates="withdrawals")
