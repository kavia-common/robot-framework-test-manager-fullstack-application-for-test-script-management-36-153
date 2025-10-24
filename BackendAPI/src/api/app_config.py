import functools
import os
from datetime import timedelta
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str
    jwt_secret: str
    jwt_expires_in: int
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str

    @property
    def jwt_expires_delta(self) -> timedelta:
        return timedelta(minutes=self.jwt_expires_in)


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./app.db"),
        jwt_secret=os.getenv("JWT_SECRET", "devsecret"),
        jwt_expires_in=int(os.getenv("JWT_EXPIRES_IN", "60")),
        minio_endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        minio_bucket=os.getenv("MINIO_BUCKET", "rf-test-manager"),
    )
