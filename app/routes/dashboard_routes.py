from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.misc import AdminDashboard, UserDashboard
from app.security import get_current_user, require_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/admin", response_model=AdminDashboard)
def admin_dashboard(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    return AdminDashboard(
        total_users=db.query(User).count(),
        total_tasks=db.query(Task).count(),
        open_tasks=db.query(Task).filter(Task.status == TaskStatus.TODO).count(),
        in_progress_tasks=db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count(),
        completed_tasks=db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count(),
        overdue_tasks=db.query(Task).filter(Task.due_date < now, Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED])).count(),
        critical_tasks=db.query(Task).filter(Task.priority == TaskPriority.CRITICAL).count(),
    )


@router.get("/user", response_model=UserDashboard)
def user_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    base = db.query(Task).filter(Task.assigned_user_id == current_user.id)
    return UserDashboard(
        my_tasks=base.count(),
        pending_tasks=base.filter(Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])).count(),
        completed_tasks=base.filter(Task.status == TaskStatus.COMPLETED).count(),
        overdue_tasks=base.filter(Task.due_date < now, Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED])).count(),
        critical_tasks=base.filter(Task.priority == TaskPriority.CRITICAL).count(),
    )
