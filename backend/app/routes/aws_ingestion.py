from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services import get_s3_service, S3Service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["aws-ingestion"])

class UploadRequest(BaseModel):
    filename: str
    content_type: str

@router.post("/aws/ingest/upload-url")
def get_upload_url(
    request: UploadRequest,
    s3_service: S3Service = Depends(get_s3_service)
):
    """
    Get a presigned URL to upload a file to the AWS Input S3 Bucket.
    Resulting S3 upload will trigger the AWS processing pipeline.
    """
    if not request.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, 
            detail="Only .pdf files are supported for AWS pipeline currently."
        )

    # Use strict typing and new service
    response = s3_service.generate_presigned_post(request.filename)
    if not response:
        logger.error(f"Failed to generate presigned URL for {request.filename}")
        raise HTTPException(
            status_code=500, 
            detail="Could not generate upload URL. Check server logs."
        )
    
    return response
