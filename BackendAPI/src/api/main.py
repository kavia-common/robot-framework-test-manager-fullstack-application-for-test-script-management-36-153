import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .app_config import get_settings
from .auth import auth_router
from .database import Base, engine
from .minio_client import get_minio_client
from .routers import cases, execute, history, logs, queue, tests
from .workers import start_background_worker

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("BackendAPI")

settings = get_settings()

# Create all tables (in real apps, use migrations)
Base.metadata.create_all(bind=engine)

# FastAPI app with metadata and tags
app = FastAPI(
    title="Robot Framework Test Manager Backend API",
    version="1.0.0",
    description="APIs for managing Robot Framework tests, cases, execution, queue, history, and logs. JWT-secured with RBAC.",
    openapi_tags=[
        {"name": "auth", "description": "Authentication and user info"},
        {"name": "tests", "description": "Test scripts CRUD"},
        {"name": "cases", "description": "Test cases CRUD"},
        {"name": "queue", "description": "Execution queue management"},
        {"name": "execute", "description": "Trigger execution"},
        {"name": "history", "description": "Run history"},
        {"name": "logs", "description": "Execution logs"},
        {"name": "health", "description": "Service health"},
    ],
)

# CORS
allow_origins = (
    [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")]
    if os.getenv("CORS_ALLOW_ORIGINS")
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """Simple health check returning 200 with static body."""
    return {"message": "Healthy"}


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(tests.router, prefix="/tests", tags=["tests"])
app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(queue.router, prefix="/queue", tags=["queue"])
app.include_router(execute.router, prefix="/execute", tags=["execute"])
app.include_router(history.router, prefix="/history", tags=["history"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])

# Start background worker to process queue on app startup
@app.on_event("startup")
def startup_event():
    # Ensure Minio bucket exists at startup
    try:
        client, bucket = get_minio_client()
        found = client.bucket_exists(bucket)
        if not found:
            client.make_bucket(bucket)
            logger.info("Created Minio bucket '%s'", bucket)
        else:
            logger.info("Minio bucket '%s' ready", bucket)
    except Exception as e:
        logger.error("Minio setup error: %s", e)

    start_background_worker()
