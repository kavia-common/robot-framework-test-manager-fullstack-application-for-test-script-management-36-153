import datetime
from typing import Tuple

from minio import Minio
from minio.error import S3Error

from .app_config import get_settings

_settings = get_settings()


# PUBLIC_INTERFACE
def get_minio_client() -> Tuple[Minio, str]:
    """Return configured Minio client and bucket name."""
    endpoint = _settings.minio_endpoint
    # Auto-detect secure False if endpoint seems local
    secure = not (endpoint.startswith("localhost") or endpoint.startswith("127.0.0.1"))
    client = Minio(
        endpoint=endpoint,
        access_key=_settings.minio_access_key,
        secret_key=_settings.minio_secret_key,
        secure=secure,
    )
    return client, _settings.minio_bucket


# PUBLIC_INTERFACE
def get_presigned_url(object_name: str, expires_seconds: int = 3600) -> str:
    """Generate a presigned URL for an object in the configured bucket."""
    client, bucket = get_minio_client()
    try:
        url = client.presigned_get_object(bucket, object_name, expires=datetime.timedelta(seconds=expires_seconds))
        return url
    except S3Error as e:
        raise RuntimeError(f"Failed to generate presigned URL: {e}")
