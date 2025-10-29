"""
Configuration settings module for the Backend API.
Manages all environment variables and application configuration.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = Field(default="Robot Framework Test Manager", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Database
    database_url: str = Field(
        ...,
        description="PostgreSQL database URL. Required environment variable."
    )
    db_pool_size: int = Field(default=20, description="Database connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")
    
    # JWT Authentication
    jwt_secret_key: str = Field(
        ...,
        description="JWT secret key. Required environment variable."
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    
    # Minio
    minio_endpoint: str = Field(
        ...,
        description="Minio endpoint. Required environment variable."
    )
    minio_access_key: str = Field(
        ...,
        description="Minio access key. Required environment variable."
    )
    minio_secret_key: str = Field(
        ...,
        description="Minio secret key. Required environment variable."
    )
    minio_secure: bool = Field(default=False, description="Use secure connection")
    minio_bucket_logs: str = Field(default="test-logs", description="Bucket for logs")
    minio_bucket_uploads: str = Field(default="test-uploads", description="Bucket for uploads")
    
    # Redis
    redis_url: str = Field(default="redis://redis:6379/0", description="Redis URL")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    # Test Execution
    max_concurrent_executions: int = Field(
        default=5,
        description="Maximum concurrent test executions"
    )
    execution_timeout_seconds: int = Field(
        default=3600,
        description="Test execution timeout in seconds"
    )
    
    # File Upload
    max_upload_size_mb: int = Field(
        default=100,
        description="Maximum upload size in MB"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
