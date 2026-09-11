"""
Routes layer: Pure HTTP routing.
Delegates business logic to the controller layer.
"""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.controllers import task_controller
from app.database import get_db
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.security import get_current_user
from app.services.audit_service import record_audit
from app.services.notification_service import create_notification
from app.schemas.task import (
    MessageResponse,
    PaginatedTaskResponse,
    TaskCreate,
    TaskAssign,
    TaskPriorityUpdate,
    TaskResponse,
    TaskStatusUpdate,
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = task_controller.create_task(db, task, current_user)
    record_audit(db, current_user.id, "Task Created", "Task", created.id)
    background_tasks.add_task(create_notification, created.assigned_user_id, f"Task assigned: {created.title}")
    return created


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
    priority_filter: Optional[TaskPriority] = Query(None, alias="priority"),
    assigned_user_id: Optional[int] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_controller.list_tasks(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assigned_user_id=assigned_user_id,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
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
    current_user: User = Depends(get_current_user),
):
    return task_controller.get_task(db, task_id, current_user)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    response_description="Updated task",
)
def update_task(
    task_id: int,
    task: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = task_controller.update_task(db, task_id, task, current_user)
    record_audit(db, current_user.id, "Task Updated", "Task", updated.id)
    if task.assigned_user_id:
        background_tasks.add_task(create_notification, updated.assigned_user_id, f"Task reassigned: {updated.title}")
    if task.status:
        background_tasks.add_task(create_notification, updated.assigned_user_id, f"Task status changed: {updated.status.value}")
    return updated


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
    current_user: User = Depends(get_current_user),
):
    task_controller.delete_task(db, task_id, current_user)
    record_audit(db, current_user.id, "Task Deleted", "Task", task_id)
    return MessageResponse(
        message=f"Task {task_id} deleted successfully"
    )


@router.put("/{task_id}/assign", response_model=TaskResponse)
def assign_task(
    task_id: int,
    payload: TaskAssign,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = task_controller.get_task(db, task_id, current_user)
    updated = task_controller.update_task(
        db,
        task_id,
        TaskUpdate(
            title=existing.title,
            description=existing.description,
            assigned_user_id=payload.assigned_user_id,
        ),
        current_user,
    )
    record_audit(db, current_user.id, "Task Assigned", "Task", task_id)
    background_tasks.add_task(create_notification, payload.assigned_user_id, f"Task assigned: {updated.title}")
    return updated


@router.put("/{task_id}/status", response_model=TaskResponse)
def change_status(
    task_id: int,
    payload: TaskStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = task_controller.get_task(db, task_id, current_user)
    updated = task_controller.update_task(
        db,
        task_id,
        TaskUpdate(
            title=existing.title,
            description=existing.description,
            status=payload.status,
        ),
        current_user,
    )
    record_audit(db, current_user.id, "Task Status Changed", "Task", task_id)
    background_tasks.add_task(create_notification, updated.assigned_user_id, f"Task status changed: {payload.status.value}")
    return updated


@router.put("/{task_id}/priority", response_model=TaskResponse)
def change_priority(
    task_id: int,
    payload: TaskPriorityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = task_controller.get_task(db, task_id, current_user)
    updated = task_controller.update_task(
        db,
        task_id,
        TaskUpdate(
            title=existing.title,
            description=existing.description,
            priority=payload.priority,
        ),
        current_user,
    )
    record_audit(db, current_user.id, "Task Priority Changed", "Task", task_id)
    return updated
