from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Numeric
from sqlalchemy.orm import relationship
from decimal import Decimal

from .base import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    username = Column(String, nullable=True)
    url = Column(String, nullable=False)
    reward = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    requires_subscription = Column(Boolean, default=False, nullable=False)

    completions = relationship("TaskCompletion", back_populates="task")


class TaskCompletion(Base):
    __tablename__ = "task_completions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)

    task = relationship("Task", back_populates="completions")
    user = relationship("User", back_populates="task_completions")