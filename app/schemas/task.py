"""
Schema layer: Pydantic models used for request validation and response
serialization. Keeping these separate from the SQLAlchemy models means
the API's public "shape" never leaks internal DB details by accident.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the task")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    assigned_user_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: Optional[datetime] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if value == "Pending":
            return TaskStatus.TODO
        return value


class TaskCreate(TaskBase):
    """Payload for creating a new task."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Write project README",
                "description": "Document setup steps and API usage",
                "assigned_user_id": 1,
                "priority": "high",
                "status": "todo",
            }
        }
    )


class TaskUpdate(BaseModel):
    """Payload for updating a task. All fields optional (partial update)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    assigned_user_id: Optional[int] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if value == "Pending":
            return TaskStatus.TODO
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "in_progress"}
        }
    )


class TaskResponse(TaskBase):
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedTaskResponse(BaseModel):
    total: int = Field(..., description="Total number of tasks matching the query")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    items: List[TaskResponse]


class MessageResponse(BaseModel):
    message: str


class TaskAssign(BaseModel):
    assigned_user_id: int


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskPriorityUpdate(BaseModel):
    priority: TaskPriority
