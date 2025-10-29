"""
Main FastAPI application with comprehensive OpenAPI documentation.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import settings
from src.database.session import init_db
from src.api.routers import auth, tests, cases, execution, queue, history
from src.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Robot Framework Test Manager API")
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")


# OpenAPI tags metadata
openapi_tags = [
    {
        "name": "Authentication",
        "description": "User authentication and session management. Supports JWT tokens for secure API access."
    },
    {
        "name": "Test Scripts",
        "description": "Manage Robot Framework test scripts. Create, read, update, and delete test script metadata."
    },
    {
        "name": "Test Cases",
        "description": "Manage test cases associated with test scripts. Configure variables and execution parameters."
    },
    {
        "name": "Execution",
        "description": "Execute test cases ad hoc or queue them for later execution."
    },
    {
        "name": "Queue",
        "description": "Manage the test execution queue. View, add, and remove queued test cases."
    },
    {
        "name": "History",
        "description": "View test execution history and access execution logs stored in Minio."
    }
]


# Create FastAPI app with metadata
app = FastAPI(
    title="Robot Framework Test Manager API",
    description="""
    Backend API for managing Robot Framework test scripts, test cases, execution, and run history.
    
    ## Features
    
    * **Authentication & Authorization**: Secure JWT-based authentication with role-based access control
    * **Test Management**: Create and manage Robot Framework test scripts and test cases
    * **Execution**: Execute tests ad hoc or schedule them via queue
    * **Queue Management**: Prioritized execution queue for batch processing
    * **Run History**: Complete audit trail of all test executions
    * **Log Storage**: Execution logs stored in Minio object storage with presigned URL access
    * **Audit Logging**: Comprehensive audit logs for security and compliance
    
    ## Authentication
    
    Most endpoints require authentication. To authenticate:
    
    1. Call `POST /api/v1/auth/login` with username and password
    2. Use the returned `access_token` in the Authorization header: `Bearer <token>`
    
    ## WebSocket Support
    
    Real-time execution updates can be subscribed to via WebSocket connections (planned feature).
    See the `/ws/executions` endpoint documentation for details on connecting and receiving updates.
    """,
    version=settings.app_version,
    openapi_tags=openapi_tags,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers with prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(tests.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")
app.include_router(execution.router, prefix="/api/v1")
app.include_router(queue.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    
    Returns service status and version information.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.get("/api/v1/docs/websocket", tags=["Documentation"])
def websocket_usage():
    """
    WebSocket usage documentation.
    
    Provides information on how to connect to and use WebSocket endpoints
    for real-time execution updates.
    
    ## Connection
    
    Connect to: `ws://host:port/ws/executions`
    
    ## Authentication
    
    Include JWT token in connection: `ws://host:port/ws/executions?token=<access_token>`
    
    ## Message Format
    
    Server sends JSON messages with execution status updates:
    
    ```json
    {
        "type": "execution_update",
        "run_id": "string",
        "status": "running|passed|failed|error",
        "timestamp": "ISO8601 datetime"
    }
    ```
    """
    return {
        "message": "WebSocket documentation",
        "endpoint": "/ws/executions",
        "authentication": "Include token as query parameter: ?token=<access_token>",
        "note": "WebSocket implementation is planned for real-time execution updates"
    }
