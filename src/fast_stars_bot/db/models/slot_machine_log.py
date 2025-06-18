from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class SlotMachineLog(Base):
    __tablename__ = "slot_machine_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    win_amount = Column(Numeric(10, 2), nullable=False, default=0)

    user = relationship("User", back_populates="slot_machine_logs")
