"""
Application entry point.
Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from config import settings
from database import Base, engine
from routes.task_routes import router as task_router

# Create DB tables on startup (fine for SQLite / small apps; use Alembic for
# real migrations in a larger production system).
Base.metadata.create_all(bind=engine)

tags_metadata = [
    {
        "name": "Tasks",
        "description": "Create, list (with search/filter/pagination), update, and delete tasks.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A simple Task Manager REST API built with **FastAPI**, **SQLAlchemy**, "
        "and **SQLite**.\n\n"
        "Supports full CRUD, keyword search, status filtering, and pagination."
    ),
    version=settings.APP_VERSION,
    openapi_tags=tags_metadata,
    contact={"name": "Backend Developer Assignment"},
    license_info={"name": "MIT"},
)


# ---- Custom OpenAPI schema (adds a couple of nice-to-haves to Swagger UI) ----
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ---- Global validation error handler (cleaner error payloads) ----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(loc) for loc in err["loc"] if loc != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )


@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


app.include_router(task_router)
