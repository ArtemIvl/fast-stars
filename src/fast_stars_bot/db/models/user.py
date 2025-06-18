from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Column, Date, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    stars = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    reg_date = Column(Date, nullable=False, default=date.today)
    is_banned = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    daily_bonus_claims = relationship("DailyBonusClaim", back_populates="user")
    subscriptions = relationship("SubscriptionLog", back_populates="user")
    basketball_logs = relationship("BasketballLog", back_populates="user")
    vip_subscriptions = relationship("VipSubscription", back_populates="user")
    promo_activations = relationship("PromoActivation", back_populates="user")
    task_completions = relationship("TaskCompletion", back_populates="user")
    referrals = relationship(
        "Referral", foreign_keys="[Referral.referrer_id]", back_populates="referrer"
    )
    referred_by = relationship(
        "Referral",
        foreign_keys="[Referral.referral_id]",
        back_populates="referral",
        uselist=False,
    )
    withdrawals = relationship("Withdrawal", back_populates="user")
    deposits = relationship("Deposit", back_populates="user")
    giveaway_tickets = relationship("GiveawayTicket", back_populates="user")
    slot_machine_logs = relationship("SlotMachineLog", back_populates="user")
