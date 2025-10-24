"""
Main FastAPI application for Robot Framework Test Manager.
Integrates all routers, middleware, and application configuration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.core.config import settings
from src.database import init_db, get_db
from src.services.auth_service import auth_service
from src.api.routers import tests, cases, execution, queue, history, logs, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting application...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
        
        # Initialize default roles
        db = next(get_db())
        auth_service.init_default_roles(db)
        logger.info("Default roles initialized")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RESTful API for managing Robot Framework test scripts, test cases, execution, queue, run history, and logs. Secured with JWT authentication and role-based access control.",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "User authentication and session management"},
        {"name": "Test Scripts", "description": "Manage Robot Framework test scripts"},
        {"name": "Test Cases", "description": "Manage test cases within test scripts"},
        {"name": "Execution", "description": "Execute test cases and manage execution"},
        {"name": "Queue", "description": "Manage test execution queue"},
        {"name": "Run History", "description": "View and manage test run history"},
        {"name": "Logs", "description": "Access execution logs"},
    ]
)

# Configure CORS
# Parse CORS origins from settings, supporting both comma-separated list and wildcard
if settings.CORS_ORIGINS == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

# If no origins specified, default to localhost for development
if not origins:
    origins = ["http://localhost:3000", "http://localhost:3001"]

logger.info(f"Configured CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(tests.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")
app.include_router(execution.router, prefix="/api/v1")
app.include_router(queue.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns service status and version information.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/api/v1/health", tags=["Health"])
async def api_health_check():
    """
    API health check endpoint.
    Returns API status for monitoring.
    """
    return {
        "status": "healthy",
        "api_version": "v1"
    }
