# Task Management System API

Backend REST API for a Task Management System using FastAPI, SQLAlchemy, Pydantic, JWT-style bearer authentication, RBAC, background notification creation, file uploads, and audit logging.

## Implemented Assignment Features

- Auth: register, login, logout, profile update, change password
- RBAC: `admin` and `user`; admins manage users and all tasks
- Users: create, list, view, update, deactivate
- Tasks: create, view, update, delete, assign, change status, change priority
- Task fields: title, description, assigned user, created by, priority, status, due date, created/updated/completed timestamps
- Workflow enforcement: `todo -> in_progress -> Completed`; cancelled/completed tasks cannot be modified, and invalid transitions are rejected
- Comments: add/list/update/delete; own-comment rule for users, admin override; closed tasks reject new comments
- Attachments: upload/list/delete with type and size validation; metadata stored in the database
- Notifications: generated with FastAPI background tasks for assignment, reassignment, status changes, comments, and completion
- Dashboards: admin and user dashboard counters
- Audit logs: important user/task/comment/attachment operations are recorded
- Search, filtering, sorting, and pagination on `GET /tasks`

## Setup

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Docs are available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The default database is SQLite for easy local review. Set `DATABASE_URL` in `.env` to a PostgreSQL or MySQL SQLAlchemy URL for those engines.

## Key Endpoints

```text
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/profile
PUT  /auth/profile
PUT  /auth/change-password

GET    /users
GET    /users/{id}
POST   /users
PUT    /users/{id}
DELETE /users/{id}

POST   /tasks
GET    /tasks?page=1&page_size=20&status=in_progress&priority=high&search=payment
GET    /tasks/{id}
PUT    /tasks/{id}
DELETE /tasks/{id}
PUT    /tasks/{id}/assign
PUT    /tasks/{id}/status
PUT    /tasks/{id}/priority

POST   /tasks/{task_id}/comments
GET    /tasks/{task_id}/comments
PUT    /comments/{id}
DELETE /comments/{id}

POST   /tasks/{task_id}/attachments
GET    /tasks/{task_id}/attachments
DELETE /attachments/{id}

GET /notifications
PUT /notifications/{id}/read
PUT /notifications/read-all

GET /dashboard/admin
GET /dashboard/user

GET /audit-logs
GET /audit-logs/{id}
```

## Authentication

Use the token returned by `/auth/register` or `/auth/login`:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/auth/profile
```

## Tests

```bash
pytest -v
```
