# Architecture Diagram

```mermaid
flowchart TD
    Client[API Client] --> FastAPI[FastAPI App]
    FastAPI --> Routes[Routes]
    Routes --> Dependencies[Auth/RBAC Dependencies]
    Routes --> Controllers[Controllers]
    Controllers --> Services[Services]
    Services --> SQLAlchemy[SQLAlchemy Session]
    SQLAlchemy --> Database[(Database)]
    Routes --> BackgroundTasks[FastAPI BackgroundTasks]
    BackgroundTasks --> Notifications[Notification Service]
    Notifications --> Database
    Services --> Audit[Audit Log Service]
    Audit --> Database
```

## Layers

- `routes/`: HTTP endpoints and dependency injection
- `controllers/`: task response orchestration and HTTP error translation
- `services/`: business rules, database operations, audit and notification helpers
- `models/`: SQLAlchemy ORM entities and relationships
- `schemas/`: Pydantic request and response models
- `security.py`: password hashing, bearer token creation/validation, RBAC dependencies
