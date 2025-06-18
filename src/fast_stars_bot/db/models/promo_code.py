from decimal import Decimal

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .base import Base


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    reward = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    max_activations = Column(Integer, nullable=False)
    activations_left = Column(Integer, nullable=False)
    is_vip = Column(Boolean, default=False)

    activations = relationship("PromoActivation", back_populates="promo_code")


class PromoActivation(Base):
    __tablename__ = "promo_activations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)

    promo_code = relationship("PromoCode", back_populates="activations")
    user = relationship("User", back_populates="promo_activations")
