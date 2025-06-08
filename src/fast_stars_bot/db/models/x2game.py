from sqlalchemy import Numeric, Integer, Column
from .base import Base

class X2Game(Base):
    __tablename__ = "x2game"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lost = Column(Numeric(10, 2), nullable=False, default=0)
    won = Column(Numeric(10, 2), nullable=False, default=0)