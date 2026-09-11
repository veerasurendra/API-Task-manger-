from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    id: int
    task_id: int
    uploaded_by_id: int
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    entity: str
    entity_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminDashboard(BaseModel):
    total_users: int
    total_tasks: int
    open_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    critical_tasks: int


class UserDashboard(BaseModel):
    my_tasks: int
    pending_tasks: int
    completed_tasks: int
    overdue_tasks: int
    critical_tasks: int
