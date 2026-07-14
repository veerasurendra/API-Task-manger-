"""
Routes layer: Pure HTTP routing.
Delegates business logic to the controller layer.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from config import settings
from controllers import task_controller
from database import get_db
from models.task import TaskStatus
from schemas.task import (
    MessageResponse,
    PaginatedTaskResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    response_description="Created task",
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    return task_controller.create_task(db, task)


@router.get(
    "",
    response_model=PaginatedTaskResponse,
    summary="List tasks",
    response_description="Paginated list of tasks",
)
def list_tasks(
    page: int = Query(
        1,
        ge=1,
        description="Page number (starts from 1)",
    ),
    page_size: Optional[int] = Query(
        None,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (default {settings.DEFAULT_PAGE_SIZE}, max {settings.MAX_PAGE_SIZE})",
    ),
    search: Optional[str] = Query(
        None,
        description="Search by title or description",
    ),
    status_filter: Optional[TaskStatus] = Query(
        None,
        alias="status",
        description="Filter by task status",
    ),
    db: Session = Depends(get_db),
):
    return task_controller.list_tasks(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status_filter,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    response_description="Task details",
)
def get_task(
    task_id: int = Path(
        ...,
        gt=0,
        description="Task ID",
    ),
    db: Session = Depends(get_db),
):
    return task_controller.get_task(db, task_id)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    response_description="Updated task",
)
def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
):
    return task_controller.update_task(db, task_id, task)


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    summary="Delete task",
    response_description="Delete confirmation",
)
def delete_task(
    task_id: int = Path(
        ...,
        gt=0,
        description="Task ID",
    ),
    db: Session = Depends(get_db),
):
    task_controller.delete_task(db, task_id)
    return MessageResponse(
        message=f"Task {task_id} deleted successfully"
    )