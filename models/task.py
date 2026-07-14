"""
Model layer: SQLAlchemy ORM model for a Task.
"""
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func

from database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(String(2000), nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
