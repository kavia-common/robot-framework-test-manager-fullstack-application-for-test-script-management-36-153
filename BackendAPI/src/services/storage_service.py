"""
Storage service for Minio object storage integration.
Handles file upload, download, and management.
"""

from minio import Minio
from minio.error import S3Error
from typing import BinaryIO
from datetime import timedelta
import io

from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Service for managing file storage in Minio."""
    
    def __init__(self):
        """Initialize Minio client."""
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure required buckets exist."""
        buckets = [settings.minio_bucket_logs, settings.minio_bucket_uploads]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Error ensuring bucket {bucket}: {str(e)}")
    
    # PUBLIC_INTERFACE
    def upload_log(self, run_id: str, content: str) -> str:
        """
        Upload test execution log to Minio.
        
        Args:
            run_id: Run ID for the log file
            content: Log content as string
            
        Returns:
            str: Object key in Minio
        """
        object_key = f"logs/{run_id}.log"
        
        try:
            data = content.encode('utf-8')
            data_stream = io.BytesIO(data)
            
            self.client.put_object(
                settings.minio_bucket_logs,
                object_key,
                data_stream,
                length=len(data),
                content_type="text/plain"
            )
            
            logger.info(f"Uploaded log for run {run_id}")
            return object_key
            
        except S3Error as e:
            logger.error(f"Error uploading log for run {run_id}: {str(e)}")
            raise
    
    # PUBLIC_INTERFACE
    def upload_file(self, file: BinaryIO, filename: str, content_type: str = "application/octet-stream") -> str:
        """
        Upload a file to Minio.
        
        Args:
            file: File object to upload
            filename: Name for the file
            content_type: MIME type of the file
            
        Returns:
            str: Object key in Minio
        """
        object_key = f"uploads/{filename}"
        
        try:
            # Get file size
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            
            self.client.put_object(
                settings.minio_bucket_uploads,
                object_key,
                file,
                length=size,
                content_type=content_type
            )
            
            logger.info(f"Uploaded file: {filename}")
            return object_key
            
        except S3Error as e:
            logger.error(f"Error uploading file {filename}: {str(e)}")
            raise
    
    # PUBLIC_INTERFACE
    def get_presigned_url(self, bucket: str, object_key: str, expires: int = 3600) -> str:
        """
        Get a presigned URL for accessing an object.
        
        Args:
            bucket: Bucket name
            object_key: Object key
            expires: URL expiration in seconds (default 1 hour)
            
        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_key,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_key}: {str(e)}")
            raise
    
    # PUBLIC_INTERFACE
    def get_log_url(self, object_key: str) -> str:
        """
        Get presigned URL for a log file.
        
        Args:
            object_key: Object key for the log
            
        Returns:
            str: Presigned URL
        """
        return self.get_presigned_url(settings.minio_bucket_logs, object_key)
    
    # PUBLIC_INTERFACE
    def delete_object(self, bucket: str, object_key: str):
        """
        Delete an object from Minio.
        
        Args:
            bucket: Bucket name
            object_key: Object key to delete
        """
        try:
            self.client.remove_object(bucket, object_key)
            logger.info(f"Deleted object: {object_key} from {bucket}")
        except S3Error as e:
            logger.error(f"Error deleting object {object_key}: {str(e)}")
            raise


# Global storage service instance
storage_service = StorageService()
