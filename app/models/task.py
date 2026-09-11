"""
Model layer: SQLAlchemy ORM model for a Task.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.attachment import Attachment
    from app.models.comment import Comment


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "Completed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    assigned_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority),
        nullable=False,
        default=TaskPriority.MEDIUM,
        index=True
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.TODO,
        index=True
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    assigned_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_user_id],
        back_populates="assigned_tasks"
    )

    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_tasks"
    )

    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        cascade="all, delete-orphan",
        back_populates="task"
    )

    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        cascade="all, delete-orphan",
        back_populates="task"
    )