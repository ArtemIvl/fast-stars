from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class DailyBonusClaim(Base):
    __tablename__ = "daily_bonus_claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    claim_date = Column(Date, nullable=False, default=date.today)
    bonus_amount = Column(Numeric(10, 2), nullable=False)
    streak = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="daily_bonus_claims")
