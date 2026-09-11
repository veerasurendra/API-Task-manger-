import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.attachment import Attachment
from app.models.task import Task
from app.models.user import User
from app.schemas.misc import AttachmentResponse
from app.schemas.task import MessageResponse
from app.security import get_current_user
from app.services.audit_service import record_audit
from app.services.task_service import ensure_authorized_task

router = APIRouter(tags=["Attachments"])
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".txt"}


@router.post("/tasks/{task_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def add_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    ensure_authorized_task(current_user, task)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type is not allowed")
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds limit")
    os.makedirs("uploads", exist_ok=True)
    storage_path = os.path.join("uploads", f"{uuid.uuid4().hex}{ext}")
    with open(storage_path, "wb") as uploaded:
        uploaded.write(content)
    attachment = Attachment(
        task_id=task_id,
        uploaded_by_id=current_user.id,
        filename=file.filename or "attachment",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        storage_path=storage_path,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    record_audit(db, current_user.id, "Attachment Added", "Attachment", attachment.id)
    return attachment


@router.get("/tasks/{task_id}/attachments", response_model=List[AttachmentResponse])
def list_attachments(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    ensure_authorized_task(current_user, task)
    return db.query(Attachment).filter(Attachment.task_id == task_id).order_by(Attachment.id.desc()).all()


@router.delete("/attachments/{attachment_id}", response_model=MessageResponse)
def delete_attachment(attachment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    ensure_authorized_task(current_user, attachment.task)
    db.delete(attachment)
    db.commit()
    record_audit(db, current_user.id, "Attachment Deleted", "Attachment", attachment_id)
    return MessageResponse(message="Attachment deleted successfully")
