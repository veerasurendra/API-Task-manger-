# Simple FastAPI Task Manager API

A simple backend REST API for managing tasks, built with **FastAPI**, **SQLAlchemy**, and **SQLite**, following an MVC-style project layout.

## Features

- Full CRUD for tasks: create, list, update, delete
- Task fields: `title`, `description`, `status` (`Pending` / `Completed`)
- Search (by title/description) and filter (by status)
- Pagination (`page`, `page_size`)
- Request validation via Pydantic, with clean error responses
- Custom Swagger / OpenAPI documentation
- Config via `.env` file
- Dockerized (Dockerfile + docker-compose)

## Project Structure (MVC-style)

```
task_manager/
├── app/
│   ├── main.py                 # App entrypoint, Swagger/OpenAPI config, startup
│   ├── config.py               # Settings loaded from .env (pydantic-settings)
│   ├── database.py             # SQLAlchemy engine/session setup
│   ├── models/                 # Model layer (SQLAlchemy ORM)
│   │   └── task.py
│   ├── schemas/                # Pydantic schemas (request/response "view" shape)
│   │   └── task.py
│   ├── services/                # Data-access layer (DB queries)
│   │   └── task_service.py
│   ├── controllers/            # Business logic layer (used by routes)
│   │   └── task_controller.py
│   └── routes/                  # HTTP routing layer (thin, delegates to controllers)
│       └── task_routes.py
├── data/                        # SQLite DB file lives here (created at runtime)
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

**Layer responsibilities:**
- **Models** – SQLAlchemy tables/columns (the data shape in the DB)
- **Schemas** – Pydantic request/response contracts (the "View" of the API)
- **Services** – raw DB queries (Create/Read/Update/Delete + filtering)
- **Controllers** – business rules, validation of query params, pagination math, HTTP error translation
- **Routes** – FastAPI `APIRouter` endpoints; stay thin and just call controllers

## Requirements

- Python 3.11+
- pip

## Setup Instructions (Local)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd task_manager
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` if you want to change the DB path, default page size, etc.

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Open Swagger UI**
   - Swagger docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Raw OpenAPI schema: http://localhost:8000/openapi.json

The SQLite database file is created automatically at `./data/tasks.db` on first run.

## Running with Docker

```bash
cp .env.example .env
docker-compose up --build
```

The API will be available at `http://localhost:8000`. The SQLite file is persisted to `./data/tasks.db` on the host via a bind-mounted volume.

To stop:
```bash
docker-compose down
```

## API Endpoints

| Method | Endpoint          | Description                                   |
|--------|-------------------|------------------------------------------------|
| POST   | `/tasks`          | Create a new task                              |
| GET    | `/tasks`          | List tasks (search, filter, pagination)        |
| GET    | `/tasks/{id}`     | Get a single task by ID                        |
| PUT    | `/tasks/{id}`     | Update a task (partial update supported)       |
| DELETE | `/tasks/{id}`     | Delete a task                                  |

### Task fields

| Field         | Type   | Notes                                  |
|---------------|--------|-----------------------------------------|
| `id`          | int    | Auto-generated                          |
| `title`       | string | Required, 1–200 chars                   |
| `description` | string | Optional, up to 2000 chars              |
| `status`      | string | `"Pending"` or `"Completed"` (default `Pending`) |
| `created_at`  | datetime | Auto-set on creation                  |
| `updated_at`  | datetime | Auto-updated on modification          |

### `GET /tasks` query parameters

| Param        | Type   | Default | Description                                      |
|--------------|--------|---------|---------------------------------------------------|
| `page`       | int    | 1       | Page number (1-indexed)                            |
| `page_size`  | int    | 10      | Items per page (max 100)                            |
| `search`     | string | –       | Case-insensitive match on title/description        |
| `status`     | string | –       | Filter by `Pending` or `Completed`                  |

Example:
```
GET /tasks?search=report&status=Pending&page=1&page_size=5
```

## Example Requests

**Create a task**
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Write README", "description": "Add setup instructions", "status": "Pending"}'
```

**List tasks (paginated)**
```bash
curl "http://localhost:8000/tasks?page=1&page_size=10"
```

**Search + filter**
```bash
curl "http://localhost:8000/tasks?search=report&status=Pending"
```

**Update a task**
```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Completed"}'
```

**Delete a task**
```bash
curl -X DELETE http://localhost:8000/tasks/1
```

## Error Handling

- **404** – Task not found (get/update/delete on a non-existent id)
- **422** – Validation error (e.g. empty title, invalid status value) with a structured `{"detail": ..., "errors": [...]}` payload
- **400** – Invalid pagination parameters (e.g. `page_size` out of allowed range)

## Notes

- Tables are created automatically on startup via `Base.metadata.create_all()`. For a production system with evolving schemas, introduce Alembic migrations instead.
- `.env` is git-ignored; only `.env.example` is committed, so secrets/config never leak into version control.
