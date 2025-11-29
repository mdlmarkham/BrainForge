"""Ingestion API routes for BrainForge."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from src.models.ingestion import ContentType, IngestionTask
from src.services.ingestion_service import IngestionService

router = APIRouter()

# Initialize ingestion service
ingestion_service = IngestionService("")  # Database URL will be configured from environment


@router.post("/pdf", status_code=status.HTTP_202_ACCEPTED)
async def ingest_pdf(
    file: UploadFile = File(...),
    source_url: Optional[str] = Form(None),
    tags: Optional[List[str]] = Form(None),
    priority: str = Form("normal")
):
    """Submit PDF for ingestion processing."""
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be PDF (application/pdf)"
        )
    
    # Validate file size (100MB limit) - handle None size
    file_size = file.size or 0
    if file_size > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF file too large (>100MB)"
        )
    
    try:
        # Handle optional tags
        tags_list = tags or []
        
        # Create ingestion task
        task = await ingestion_service.create_ingestion_task(
            content_type=ContentType.PDF,
            source_url=source_url,
            file_name=file.filename,
            file_size=file_size,
            tags=tags_list,
            priority=priority,
            created_by="api_user"  # Would come from authentication
        )
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process PDF asynchronously
        asyncio.create_task(ingestion_service.process_pdf_task(task.id, temp_file_path))
        
        return {
            "task_id": task.id,
            "status": "accepted",
            "estimated_completion": task.estimated_completion,
            "message": "PDF accepted for processing"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.get("/pdf/{task_id}")
async def get_pdf_processing_status(task_id: UUID):
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
async def retry_pdf_processing(task_id: UUID):
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
    files: List[UploadFile] = File(...),
    batch_name: Optional[str] = Form(None)
):
    """Submit multiple PDFs for batch processing."""
    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No PDF files provided"
        )
    
    # Validate all files are PDFs
    for file in files:
        if not file.content_type == "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} is not a PDF"
            )
        file_size = file.size or 0
        if file_size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"PDF file {file.filename} too large (>100MB)"
            )
    
    try:
        task_ids = []
        
        for file in files:
            # Create ingestion task for each PDF
            file_size = file.size or 0
            task = await ingestion_service.create_ingestion_task(
                content_type=ContentType.PDF,
                file_name=file.filename,
                file_size=file_size,
                tags=["batch_processing"],
                priority="normal",
                created_by="api_user"
            )
            
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF batch: {str(e)}"
        )


@router.post("/ingestion")
async def ingest_content():
    """Ingest external content (generic endpoint)."""
    return {"message": "Generic ingestion endpoint - to be implemented for other content types"}
