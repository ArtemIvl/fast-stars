from sqlalchemy import Column, String, Numeric
from .base import Base

class GameSetting(Base):
    __tablename__ = "game_settings"

    key = Column(String, primary_key=True)
    value = Column(Numeric(5, 2), nullable=False)