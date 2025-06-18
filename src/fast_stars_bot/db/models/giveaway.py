from datetime import timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import Base


class Giveaway(Base):
    __tablename__ = "giveaways"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    is_finished = Column(Boolean, nullable=False, default=False)
    prize_pool = Column(Numeric(10, 2), nullable=False)
    channel_link = Column(String)
    username = Column(String)
    num_of_winners = Column(Integer, nullable=False)

    tickets = relationship("GiveawayTicket", back_populates="giveaway")


class GiveawayTicket(Base):
    __tablename__ = "giveaway_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    giveaway_id = Column(Integer, ForeignKey("giveaways.id"), nullable=False)

    user = relationship("User", back_populates="giveaway_tickets")
    giveaway = relationship("Giveaway", back_populates="tickets")
