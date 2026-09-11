import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DATABASE_URL"] = "sqlite:///./test_task_manager.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def register_user(role="user"):
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "name": f"{role.title()} {suffix}",
        "email": f"{role}-{suffix}@example.com",
        "password": "secret123",
        "role": role,
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    return data["user"], {"Authorization": f"Bearer {data['access_token']}"}


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200


def test_auth_profile_and_task_crud():
    user, headers = register_user()
    profile = client.get("/auth/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["id"] == user["id"]

    payload = {
        "title": "Test Task",
        "description": "A test",
        "assigned_user_id": user["id"],
        "priority": "high",
        "status": "todo",
    }
    response = client.post("/tasks", json=payload, headers=headers)
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Test Task"
    assert task["status"] == "todo"
    assert task["created_by_id"] == user["id"]

    list_response = client.get("/tasks?page=1&page_size=2&priority=high", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    update_response = client.put(f"/tasks/{task['id']}", json={"title": "New title"}, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "New title"

    delete_response = client.delete(f"/tasks/{task['id']}", headers=headers)
    assert delete_response.status_code == 200


def test_status_transition_rules_and_closed_task_comment_rule():
    user, headers = register_user()
    task = client.post(
        "/tasks",
        json={"title": "Workflow", "assigned_user_id": user["id"]},
        headers=headers,
    ).json()

    invalid = client.put(f"/tasks/{task['id']}/status", json={"status": "Completed"}, headers=headers)
    assert invalid.status_code == 400

    assert client.put(f"/tasks/{task['id']}/status", json={"status": "in_progress"}, headers=headers).status_code == 200
    completed = client.put(f"/tasks/{task['id']}/status", json={"status": "Completed"}, headers=headers)
    assert completed.status_code == 200

    reopen = client.put(f"/tasks/{task['id']}/status", json={"status": "todo"}, headers=headers)
    assert reopen.status_code == 400

    comment = client.post(
        f"/tasks/{task['id']}/comments",
        json={"content": "Too late"},
        headers=headers,
    )
    assert comment.status_code == 400


def test_admin_can_manage_users_and_audit_logs():
    admin, admin_headers = register_user("admin")
    user_payload = {
        "name": "Managed User",
        "email": f"managed-{uuid.uuid4().hex[:8]}@example.com",
        "password": "secret123",
        "role": "user",
    }
    created = client.post("/users", json=user_payload, headers=admin_headers)
    assert created.status_code == 201
    managed_user_id = created.json()["id"]

    deactivated = client.delete(f"/users/{managed_user_id}", headers=admin_headers)
    assert deactivated.status_code == 200

    audit_logs = client.get("/audit-logs", headers=admin_headers)
    assert audit_logs.status_code == 200
    assert any(log["action"] == "User Deactivated" for log in audit_logs.json())

    dashboard = client.get("/dashboard/admin", headers=admin_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_users"] >= 2


def test_unauthenticated_requests_are_rejected():
    response = client.get("/tasks")
    assert response.status_code == 403
