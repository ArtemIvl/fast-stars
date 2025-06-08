from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Referral(Base):
    __tablename__ = 'referrals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    referral_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    referral = relationship('User', foreign_keys=[referral_id], back_populates='referred_by')
    referrer = relationship('User', foreign_keys=[referrer_id], back_populates='referrals')