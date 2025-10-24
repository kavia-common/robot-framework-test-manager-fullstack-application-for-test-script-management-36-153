"""
Storage service for managing files in MinIO.
Handles upload, download, and retrieval of test logs and large files.
"""
from minio import Minio
from minio.error import S3Error
from io import BytesIO
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for interacting with MinIO object storage"""
    
    def __init__(self):
        """Initialize MinIO client configuration"""
        self.client = None
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._initialized = False
    
    def _initialize(self):
        """Initialize MinIO client connection (lazy initialization)"""
        if self._initialized:
            return
        
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self._ensure_bucket_exists()
            self._initialized = True
            logger.info("MinIO storage service initialized")
        except Exception as e:
            logger.error(f"Error initializing MinIO client: {e}")
            raise
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def upload_log(self, object_name: str, data: bytes) -> str:
        """
        Upload log data to MinIO.
        
        Args:
            object_name: Name of the object in MinIO
            data: Log data as bytes
            
        Returns:
            The path/URL to the uploaded object
            
        Raises:
            S3Error: If upload fails
        """
        self._initialize()
        try:
            data_stream = BytesIO(data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type="text/plain"
            )
            logger.info(f"Uploaded log: {object_name}")
            return f"{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading log: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def get_log_url(self, object_name: str, expires_in_seconds: int = 3600) -> str:
        """
        Get a presigned URL for downloading a log file.
        
        Args:
            object_name: Name of the object in MinIO
            expires_in_seconds: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL for downloading the file
            
        Raises:
            S3Error: If URL generation fails
        """
        self._initialize()
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires_in_seconds
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def download_log(self, object_name: str) -> bytes:
        """
        Download log data from MinIO.
        
        Args:
            object_name: Name of the object in MinIO
            
        Returns:
            Log data as bytes
            
        Raises:
            S3Error: If download fails
        """
        self._initialize()
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading log: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def delete_log(self, object_name: str) -> bool:
        """
        Delete a log file from MinIO.
        
        Args:
            object_name: Name of the object in MinIO
            
        Returns:
            True if deletion was successful
            
        Raises:
            S3Error: If deletion fails
        """
        self._initialize()
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted log: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting log: {e}")
            raise


# Global storage service instance
storage_service = StorageService()
