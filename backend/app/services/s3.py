"""Service for interacting with AWS S3."""

import boto3
import logging
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List

from core.config import get_settings

logger = logging.getLogger(__name__)

class S3Service:
    """Service for S3 interactions."""

    def __init__(self):
        """Initialize S3 client using settings."""
        self.settings = get_settings()
        self.s3_client = boto3.client(
            "s3", 
            region_name=self.settings.aws_region,
            aws_access_key_id=getattr(self.settings, 'aws_access_key_id', None),
            aws_secret_access_key=getattr(self.settings, 'aws_secret_access_key', None)
        )
        self.input_bucket = self.settings.input_bucket_name
        self.output_bucket = self.settings.output_bucket_name

    def generate_presigned_post(
        self, 
        object_name: str, 
        expiration: int = 3600,
        max_size_mb: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate a presigned URL S3 POST request to upload a file.

        Args:
            object_name: S3 object key (filename)
            expiration: Time in seconds for the presigned URL to remain valid
            max_size_mb: Maximum file size in MB. If None, uses setting.

        Returns:
            Dictionary with 'url' and 'fields' to be used for POST request,
            or None if error.
        """
        max_size_bytes = (max_size_mb or self.settings.max_file_size_mb) * 1024 * 1024

        try:
            # Note: explicit ACLs can conflict with "Bucket Owner Enforced" settings
            # We rely on bucket-level security policies instead.
            response = self.s3_client.generate_presigned_post(
                Bucket=self.input_bucket,
                Key=object_name,
                Conditions=[
                    ["content-length-range", 0, max_size_bytes]
                ],
                ExpiresIn=expiration
            )
            return response
        except ClientError:
            logger.exception(f"Failed to generate presigned URL for {object_name}")
            return None

    def check_bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists and is accessible.
        
        Args:
            bucket_name: Name of the bucket to check.
            
        Returns:
            True if bucket exists/accessible, False otherwise.
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            logger.error(f"Error checking bucket {bucket_name}: {e}")
            return False

# Global instance for single-client reuse
_s3_service: Optional[S3Service] = None

def get_s3_service() -> S3Service:
    """Get or create global S3Service instance."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
