"""
Application entry point.
Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
import app.models
from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router
from app.routes.task_routes import router as task_router
from app.routes.comment_routes import router as comment_router
from app.routes.attachment_routes import router as attachment_router
from app.routes.notification_routes import router as notification_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.audit_routes import router as audit_router

# Create DB tables on startup (fine for SQLite / small apps; use Alembic for
# real migrations in a larger production system).
Base.metadata.create_all(bind=engine)

tags_metadata = [
    {
        "name": "Tasks",
        "description": "Create, assign, list, update, prioritize, and delete tasks.",
    },
]

application = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Task Management System REST API built with **FastAPI**, **SQLAlchemy**, "
        "Pydantic, JWT-style bearer authentication, RBAC, comments, attachments, "
        "notifications, dashboards, and audit logs."
    ),
    version=settings.APP_VERSION,
    openapi_tags=tags_metadata,
    contact={"name": "Backend Developer Assignment"},
    license_info={"name": "MIT"},
)
application.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Custom OpenAPI schema (adds a couple of nice-to-haves to Swagger UI) ----
def custom_openapi():
    openapi_schema = getattr(application, "openapi_schema", None)
    if openapi_schema:
        return openapi_schema

    openapi_schema = get_openapi(
        title=application.title,
        version=application.version,
        description=application.description,
        routes=application.routes,
        tags=tags_metadata,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    setattr(application, "openapi_schema", openapi_schema)
    return openapi_schema


application.openapi = custom_openapi


# ---- Global validation error handler (cleaner error payloads) ----
@application.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(loc) for loc in err["loc"] if loc != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )


@application.get("/", tags=["Health"], summary="Health check")
def root():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


application.include_router(auth_router)
application.include_router(user_router)
application.include_router(task_router)
application.include_router(comment_router)
application.include_router(attachment_router)
application.include_router(notification_router)
application.include_router(dashboard_router)
application.include_router(audit_router)

# Uvicorn expects the conventional ``app`` export; keep it separate from the
# package name imported by ``import app.models`` above.
app = application
