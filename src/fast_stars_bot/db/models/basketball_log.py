from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class BasketballLog(Base):
    __tablename__ = "basketball_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bet = Column(Numeric(10, 2), nullable=False)
    result = Column(Boolean, nullable=False)

    user = relationship("User", back_populates="basketball_logs")
