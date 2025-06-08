from sqlalchemy import Column, Integer, Numeric, ForeignKey, Enum, DateTime
from datetime import datetime, timezone
import enum
from .base import Base

class GameStatus(enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELED = "canceled"

class CubeGame(Base):
    __tablename__ = "cube_games"

    id = Column(Integer, primary_key=True, index=True)
    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(GameStatus), default=GameStatus.WAITING, nullable=False)
    bet = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)