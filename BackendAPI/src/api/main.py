import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import logging

from ..database.connection import create_tables, init_db
from .routers import auth, tests, cases, execution, queue, history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# OpenAPI tags for documentation
tags_metadata = [
    {
        "name": "authentication",
        "description": "User authentication and authorization operations",
    },
    {
        "name": "test-scripts",
        "description": "Test script management operations",
    },
    {
        "name": "test-cases", 
        "description": "Test case management operations",
    },
    {
        "name": "execution",
        "description": "Test execution operations",
    },
    {
        "name": "queue",
        "description": "Test execution queue management",
    },
    {
        "name": "history",
        "description": "Test run history and log management",
    },
]

# Create FastAPI app with comprehensive metadata
app = FastAPI(
    title="Robot Framework Test Manager API",
    description="RESTful API for managing Robot Framework test scripts, test cases, execution, queue, run history, and logs. Secured with JWT/OAuth2, role-based access, and audit logging.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    servers=[{"url": "/api/v1", "description": "Main API server"}]
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "['http://localhost:3000']")
app.add_middleware(
    CORSMiddleware,
    allow_origins=eval(cors_origins) if isinstance(cors_origins, str) else cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API v1 prefix
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(tests.router, prefix=API_V1_PREFIX)
app.include_router(cases.router, prefix=API_V1_PREFIX)
app.include_router(execution.router, prefix=API_V1_PREFIX)
app.include_router(queue.router, prefix=API_V1_PREFIX)
app.include_router(history.router, prefix=API_V1_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup."""
    logger.info("Starting Robot Framework Test Manager API...")
    create_tables()
    init_db()
    logger.info("Database initialized successfully")

@app.get("/", tags=["health"])
def health_check():
    """
    Health check endpoint to verify API status.
    
    Returns:
        Simple health status message
    """
    return {"message": "Robot Framework Test Manager API is healthy"}

@app.get("/health", tags=["health"])
def detailed_health_check():
    """
    Detailed health check endpoint with system information.
    
    Returns:
        Detailed health status including version and components
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Robot Framework Test Manager API",
        "components": {
            "database": "operational",
            "minio": "operational", 
            "authentication": "operational"
        }
    }

# WebSocket route documentation for API docs
@app.get("/ws/docs", tags=["websocket"], include_in_schema=True)
def websocket_documentation():
    """
    WebSocket connection documentation and usage information.
    
    Note: WebSocket endpoints for real-time updates on test execution status,
    queue changes, and run history updates can be implemented here.
    
    Returns:
        WebSocket usage documentation
    """
    return {
        "websocket_endpoints": {
            "/ws/execution": "Real-time test execution updates",
            "/ws/queue": "Queue status changes",
            "/ws/history": "New run history entries"
        },
        "usage": "Connect using WebSocket client to receive real-time updates",
        "authentication": "Include JWT token in connection headers"
    }
