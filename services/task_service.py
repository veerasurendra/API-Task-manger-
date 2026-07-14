"""
Service layer: encapsulates all direct database access for Task records.
Controllers call into this layer instead of touching the ORM/session directly.
"""
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.task import Task, TaskStatus
from schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, task_data: TaskCreate) -> Task:
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    status_filter: Optional[TaskStatus] = None,
) -> Tuple[List[Task], int]:
    """
    Returns a tuple of (tasks for the requested page, total matching count).
    Supports:
      - search: case-insensitive match against title or description
      - status_filter: exact match on status (Pending / Completed)
    """
    query = db.query(Task)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(Task.title.ilike(like_pattern), Task.description.ilike(like_pattern))
        )

    if status_filter:
        query = query.filter(Task.status == status_filter)

    total = query.count()

    items = (
        query.order_by(Task.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
    task = get_task(db, task_id)
    if not task:
        return None

    update_fields = task_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True
