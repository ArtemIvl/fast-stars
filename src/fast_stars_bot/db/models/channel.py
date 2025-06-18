from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)
    link = Column(String, nullable=False, unique=True)
    requires_subscription = Column(Boolean, default=False)

    subscribers = relationship("SubscriptionLog", back_populates="channel")
