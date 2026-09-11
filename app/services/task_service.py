"""
Service layer: encapsulates all direct database access for Task records.
Controllers call into this layer instead of touching the ORM/session directly.
"""
from datetime import datetime, timezone
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User, UserStatus
from app.schemas.task import TaskCreate, TaskUpdate


ALLOWED_STATUS_TRANSITIONS = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}


def ensure_assignable(db: Session, user_id: Optional[int]) -> None:
    if user_id is None:
        return
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive users cannot receive new tasks")


def ensure_task_mutable(task: Task) -> None:
    if task.status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Completed or cancelled tasks cannot be modified")


def ensure_authorized_task(user: User, task: Task) -> None:
    if user.role.value == "admin":
        return
    if task.created_by_id != user.id and task.assigned_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this task")


def create_task(db: Session, task_data: TaskCreate, created_by: User) -> Task:
    ensure_assignable(db, task_data.assigned_user_id)
    task = Task(
        title=task_data.title,
        description=task_data.description,
        assigned_user_id=task_data.assigned_user_id,
        created_by_id=created_by.id,
        priority=task_data.priority,
        status=task_data.status,
        due_date=task_data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    status_filter: Optional[TaskStatus] = None,
    priority_filter: Optional[TaskPriority] = None,
    assigned_user_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> Tuple[List[Task], int]:
    """
    Returns a tuple of (tasks for the requested page, total matching count).
    Supports:
      - search: case-insensitive match against title or description
      - status_filter: exact match on status (Pending / Completed)
    """
    query = db.query(Task)
    if user.role.value != "admin":
        query = query.filter(or_(Task.created_by_id == user.id, Task.assigned_user_id == user.id))

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(Task.title.ilike(like_pattern), Task.description.ilike(like_pattern))
        )

    if status_filter:
        query = query.filter(Task.status == status_filter)
    if priority_filter:
        query = query.filter(Task.priority == priority_filter)
    if assigned_user_id:
        query = query.filter(Task.assigned_user_id == assigned_user_id)

    total = query.count()
    sort_column = getattr(Task, sort_by, Task.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    items = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_task(db: Session, task_id: int, task_data: TaskUpdate, user: User) -> Optional[Task]:
    task = get_task(db, task_id)
    if not task:
        return None
    ensure_authorized_task(user, task)
    ensure_task_mutable(task)

    update_fields = task_data.model_dump(exclude_unset=True)
    if "assigned_user_id" in update_fields:
        ensure_assignable(db, update_fields["assigned_user_id"])
    if "status" in update_fields:
        validate_status_transition(task.status, update_fields["status"])
        if update_fields["status"] == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
    for field, value in update_fields.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, user: User) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    ensure_authorized_task(user, task)
    db.delete(task)
    db.commit()
    return True


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    if current == new:
        return
    if new not in ALLOWED_STATUS_TRANSITIONS[current]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {current.value} to {new.value}",
        )
