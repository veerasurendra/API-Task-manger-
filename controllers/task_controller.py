"""
Controller layer: sits between the routes (HTTP layer) and the service
(DB layer). Handles business rules, error translation (raising HTTPException
with the right status codes), and building response payloads such as
pagination metadata.
"""
import math
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from config import settings
from models.task import TaskStatus
from schemas.task import TaskCreate, TaskUpdate, TaskResponse, PaginatedTaskResponse
from services import task_service


def create_task(db: Session, task_data: TaskCreate) -> TaskResponse:
    task = task_service.create_task(db, task_data)
    return TaskResponse.model_validate(task)


def list_tasks(
    db: Session,
    page: int = 1,
    page_size: Optional[int] = None,
    search: Optional[str] = None,
    status_filter: Optional[TaskStatus] = None,
) -> PaginatedTaskResponse:
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page must be >= 1")

    page_size = page_size or settings.DEFAULT_PAGE_SIZE
    if page_size < 1 or page_size > settings.MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"page_size must be between 1 and {settings.MAX_PAGE_SIZE}",
        )

    items, total = task_service.get_tasks(
        db, page=page, page_size=page_size, search=search, status_filter=status_filter
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedTaskResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[TaskResponse.model_validate(t) for t in items],
    )


def get_task(db: Session, task_id: int) -> TaskResponse:
    task = task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")
    return TaskResponse.model_validate(task)


def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> TaskResponse:
    task = task_service.update_task(db, task_id, task_data)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")
    return TaskResponse.model_validate(task)


def delete_task(db: Session, task_id: int) -> None:
    deleted = task_service.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")
