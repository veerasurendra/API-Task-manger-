from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.misc import AuditLogResponse
from app.security import require_admin

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(AuditLog).order_by(AuditLog.id.desc()).all()


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(log_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log
