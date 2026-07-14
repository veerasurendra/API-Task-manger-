"""
Schema layer: Pydantic models used for request validation and response
serialization. Keeping these separate from the SQLAlchemy models means
the API's public "shape" never leaks internal DB details by accident.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from models.task import TaskStatus


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the task")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Pending or Completed")


class TaskCreate(TaskBase):
    """Payload for creating a new task."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Write project README",
                "description": "Document setup steps and API usage",
                "status": "Pending",
            }
        }
    )


class TaskUpdate(BaseModel):
    """Payload for updating a task. All fields optional (partial update)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "Completed"}
        }
    )


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedTaskResponse(BaseModel):
    total: int = Field(..., description="Total number of tasks matching the query")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    items: List[TaskResponse]


class MessageResponse(BaseModel):
    message: str
