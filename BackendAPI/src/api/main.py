import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.database.connection import create_tables, init_db
from src.api.routers import tests, cases, execution, queue, history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAPI tags for documentation
tags_metadata = [
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

# Create FastAPI app without security schemes
app = FastAPI(
    title="Robot Framework Test Manager API",
    description="RESTful API for managing Robot Framework test scripts, test cases, execution, queue, run history, and logs. All endpoints are public with no authentication required.",
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

app.include_router(tests.router, prefix=API_V1_PREFIX)
app.include_router(cases.router, prefix=API_V1_PREFIX)
app.include_router(execution.router, prefix=API_V1_PREFIX)
app.include_router(queue.router, prefix=API_V1_PREFIX)
app.include_router(history.router, prefix=API_V1_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup."""
    logger.info("Starting Robot Framework Test Manager API...")
    try:
        create_tables()
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed (this is expected if database is not running): {e}")
        logger.info("API will start without database - some endpoints may not work")

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
            "database": "check connection",
            "minio": "check connection"
        }
    }
