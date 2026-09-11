from app.database import SessionLocal
from app.models.notification import Notification


def create_notification(user_id: int | None, message: str) -> None:
    if user_id is None:
        return
    db = SessionLocal()
    try:
        notification = Notification(user_id=user_id, message=message)
        db.add(notification)
        db.commit()
    finally:
        db.close()
