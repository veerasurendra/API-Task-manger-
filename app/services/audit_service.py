from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit(db: Session, user_id: int | None, action: str, entity: str, entity_id: int) -> AuditLog:
    log = AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
