from typing import List, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.comment import Comment
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.schemas.task import MessageResponse
from app.security import get_current_user
from app.services.audit_service import record_audit
from app.services.notification_service import create_notification
from app.services.task_service import ensure_authorized_task

router = APIRouter(tags=["Comments"])


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(
    task_id: int,
    payload: CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    ensure_authorized_task(current_user, task)
    if task.status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
        raise HTTPException(status_code=400, detail="Completed/cancelled tasks cannot receive new comments")
    comment = Comment(task_id=task_id, user_id=current_user.id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    record_audit(db, current_user.id, "Comment Added", "Comment", comment.id)
    background_tasks.add_task(
        create_notification,
        cast(int | None, task.assigned_user_id),
        f"Comment added to task: {task.title}",
    )
    return comment


@router.get("/tasks/{task_id}/comments", response_model=List[CommentResponse])
def list_comments(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    ensure_authorized_task(current_user, task)
    return db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.id.desc()).all()


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if current_user.role.value != "admin" and comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Users can only modify their own comments")
    comment.content = payload.content
    db.commit()
    db.refresh(comment)
    record_audit(db, current_user.id, "Comment Updated", "Comment", comment.id)
    return comment


@router.delete("/comments/{comment_id}", response_model=MessageResponse)
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if current_user.role.value != "admin" and comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Users can only modify their own comments")
    db.delete(comment)
    db.commit()
    record_audit(db, current_user.id, "Comment Deleted", "Comment", comment_id)
    return MessageResponse(message="Comment deleted successfully")
