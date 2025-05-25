from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .base import Base

class DepositStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"

class Deposit(Base):
    __tablename__ = 'deposits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    stars = Column(Numeric(10, 2), nullable=False)
    ton = Column(Numeric(10, 6), nullable=False)
    comment = Column(String, nullable=False)
    status = Column(Enum(DepositStatus), default=DepositStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="deposits")