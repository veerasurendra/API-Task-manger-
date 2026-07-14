"""
Basic tests for the Task Manager API using FastAPI's TestClient.

Run with: pytest -v
Uses a separate SQLite file so it doesn't touch dev data.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///./test_task_manager.db"

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200


def test_create_task():
    payload = {"title": "Test Task", "description": "A test", "status": "Pending"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "Pending"
    assert "id" in data


def test_list_tasks_pagination():
    for i in range(3):
        client.post("/tasks", json={"title": f"Task {i}", "status": "Pending"})
    response = client.get("/tasks?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total"] >= 3


def test_search_and_filter():
    client.post(
        "/tasks",
        json={"title": "Buy groceries", "status": "Completed"},
    )
    response = client.get("/tasks?search=groceries")
    assert response.status_code == 200
    data = response.json()
    assert any("groceries" in t["title"].lower() for t in data["items"])

    response = client.get("/tasks?status=Completed")
    assert response.status_code == 200
    data = response.json()
    assert all(t["status"] == "Completed" for t in data["items"])


def test_update_task():
    create_resp = client.post("/tasks", json={"title": "Old title"})
    task_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/tasks/{task_id}", json={"title": "New title", "status": "Completed"}
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "New title"
    assert data["status"] == "Completed"


def test_get_nonexistent_task():
    response = client.get("/tasks/999999")
    assert response.status_code == 404


def test_delete_task():
    create_resp = client.post("/tasks", json={"title": "To delete"})
    task_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/tasks/{task_id}")
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404


def test_invalid_task_creation():
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422
