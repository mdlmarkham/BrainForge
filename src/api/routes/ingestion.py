"""Ingestion API routes for BrainForge."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.models.ingestion import ContentType
from src.models.orm.user import User
from src.services.ingestion_service import IngestionService

from ..dependencies import CurrentUser
from ..security.file_validation import file_validator


async def with_timeout(coroutine, timeout_seconds: int = 30):
    """Execute a coroutine with a timeout."""
    try:
        return await asyncio.wait_for(coroutine, timeout=timeout_seconds)
    except TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"Request timeout. Maximum allowed: {timeout_seconds} seconds"
        )

router = APIRouter()

# Initialize ingestion service
ingestion_service = IngestionService("")  # Database URL will be configured from environment


@router.post("/pdf", status_code=status.HTTP_202_ACCEPTED)
async def ingest_pdf(
    file: UploadFile = File(...),
    source_url: str | None = Form(None),
    tags: list[str] | None = Form(None),
    priority: str = Form("normal"),
    current_user: User = CurrentUser
):
    """Submit PDF for ingestion processing."""
    # Validate file using comprehensive security validation
    try:
        file_type, file_hash = await file_validator.validate_upload_file(file, allowed_types=['pdf'])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {str(e)}"
        )

    try:
        # Handle optional tags
        tags_list = tags or []

        # Create ingestion task with timeout protection
        task = await with_timeout(
            ingestion_service.create_ingestion_task(
                content_type=ContentType.PDF,
                source_url=source_url,
                file_name=file_validator.sanitize_filename(file.filename),
                file_size=file.size or 0,
                file_hash=file_hash,
                tags=tags_list,
                priority=priority,
                created_by=current_user.username
            ),
            timeout_seconds=30
        )

        # Save uploaded file to temporary location with timeout
        async def save_file():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                content = await file.read()
                temp_file.write(content)
                return temp_file.name

        temp_file_path = await with_timeout(save_file(), timeout_seconds=30)

        # Process PDF asynchronously
        asyncio.create_task(ingestion_service.process_pdf_task(task.id, temp_file_path))

        return {
            "task_id": task.id,
            "status": "accepted",
            "estimated_completion": task.estimated_completion,
            "message": "PDF accepted for processing"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.get("/pdf/{task_id}")
async def get_pdf_processing_status(
    task_id: UUID,
    current_user: User = CurrentUser
):
    """Get PDF processing status and results."""
    try:
        status_result = await ingestion_service.get_task_status(task_id)

        if "error" in status_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=status_result["error"]
            )

        return status_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )


@router.post("/pdf/{task_id}/retry")
async def retry_pdf_processing(
    task_id: UUID,
    current_user: User = CurrentUser
):
    """Retry failed PDF processing."""
    try:
        # This would implement retry logic for failed tasks
        # For now, return a placeholder response
        return {
            "task_id": task_id,
            "status": "retry_initiated",
            "message": "Retry processing initiated"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry processing: {str(e)}"
        )


@router.post("/pdf/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_pdf_batch(
    files: list[UploadFile] = File(...),
    batch_name: str | None = Form(None),
    current_user: User = CurrentUser
):
    """Submit multiple PDFs for batch processing."""
    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No PDF files provided"
        )

    # Validate all files using comprehensive security validation
    file_hashes = []
    for file in files:
        try:
            file_type, file_hash = await file_validator.validate_upload_file(file, allowed_types=['pdf'])
            file_hashes.append(file_hash)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} validation failed: {str(e)}"
            )

    try:
        task_ids = []

        for i, file in enumerate(files):
            # Create ingestion task for each PDF with timeout protection
            task = await with_timeout(
                ingestion_service.create_ingestion_task(
                    content_type=ContentType.PDF,
                    file_name=file_validator.sanitize_filename(file.filename),
                    file_size=file.size or 0,
                    file_hash=file_hashes[i],
                    tags=["batch_processing"],
                    priority="normal",
                    created_by=current_user.username
                ),
                timeout_seconds=30
            )

            # Save uploaded file to temporary location with timeout
            async def save_file():
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    return temp_file.name

            temp_file_path = await with_timeout(save_file(), timeout_seconds=30)

            # Process PDF asynchronously
            asyncio.create_task(ingestion_service.process_pdf_task(task.id, temp_file_path))
            task_ids.append(str(task.id))

        return {
            "batch_id": str(UUID(int=len(task_ids))),  # Simple batch ID generation
            "task_ids": task_ids,
            "task_count": len(task_ids),
            "estimated_completion": datetime.now() + timedelta(minutes=len(task_ids) * 2),
            "message": f"Batch processing accepted for {len(task_ids)} PDFs"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF batch: {str(e)}"
        )


@router.post("/ingestion")
async def ingest_content(
    current_user: User = CurrentUser
):
    """Ingest external content (generic endpoint)."""
    return {"message": "Generic ingestion endpoint - to be implemented for other content types"}
