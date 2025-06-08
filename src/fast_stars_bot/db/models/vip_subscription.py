from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base


class VipSubscription(Base):
    __tablename__ = "vip_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="vip_subscriptions")
