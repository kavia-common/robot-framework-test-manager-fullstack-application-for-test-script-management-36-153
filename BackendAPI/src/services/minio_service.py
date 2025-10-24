import os
from typing import BinaryIO
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)

class MinIOService:
    """Service for managing file operations with MinIO object storage."""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "test-files")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the configured bucket exists, create if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def upload_file(self, file_data: BinaryIO, object_name: str, content_type: str = "application/octet-stream") -> str:
        """
        Upload a file to MinIO.
        
        Args:
            file_data: File data to upload
            object_name: Name for the object in MinIO
            content_type: MIME type of the file
            
        Returns:
            The object name/path in MinIO
            
        Raises:
            S3Error: If upload fails
        """
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                file_size,
                content_type=content_type
            )
            
            logger.info(f"Successfully uploaded {object_name} to bucket {self.bucket_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file {object_name}: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def download_file(self, object_name: str) -> bytes:
        """
        Download a file from MinIO.
        
        Args:
            object_name: Name of the object to download
            
        Returns:
            File data as bytes
            
        Raises:
            S3Error: If download fails
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Successfully downloaded {object_name} from bucket {self.bucket_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from MinIO.
        
        Args:
            object_name: Name of the object to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Successfully deleted {object_name} from bucket {self.bucket_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {e}")
            return False
    
    # PUBLIC_INTERFACE
    def get_file_url(self, object_name: str, expires_in_seconds: int = 3600) -> str:
        """
        Get a presigned URL for accessing a file.
        
        Args:
            object_name: Name of the object
            expires_in_seconds: URL expiration time in seconds
            
        Returns:
            Presigned URL for the file
            
        Raises:
            S3Error: If URL generation fails
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires_in_seconds)
            )
            return url
            
        except S3Error as e:
            logger.error(f"Error generating URL for {object_name}: {e}")
            raise
    
    # PUBLIC_INTERFACE
    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in MinIO.
        
        Args:
            object_name: Name of the object to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    # PUBLIC_INTERFACE
    def list_files(self, prefix: str = "") -> list:
        """
        List files in the bucket with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
            
        except S3Error as e:
            logger.error(f"Error listing files with prefix {prefix}: {e}")
            return []

# Global instance
minio_service = MinIOService()
