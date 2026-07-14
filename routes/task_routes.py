"""
Routes layer: pure HTTP routing. Delegates everything to the controller.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.task import TaskStatus
from schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    PaginatedTaskResponse,
    MessageResponse,
)
from controllers import task_controller

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    return task_controller.create_task(db, task)


@router.get(
    "",
    response_model=PaginatedTaskResponse,
    summary="List tasks (supports pagination, search, and status filter)",
)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page (default 10, max 100)"),
    search: Optional[str] = Query(None, description="Search text matched against title/description"),
    status_filter: Optional[TaskStatus] = Query(
        None, alias="status", description="Filter by status: Pending or Completed"
    ),
    db: Session = Depends(get_db),
):
    return task_controller.list_tasks(
        db, page=page, page_size=page_size, search=search, status_filter=status_filter
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task by ID",
)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return task_controller.get_task(db, task_id)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task (partial updates supported)",
)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    return task_controller.update_task(db, task_id, task)


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    summary="Delete a task",
)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task_controller.delete_task(db, task_id)
    return MessageResponse(message=f"Task {task_id} deleted successfully")
