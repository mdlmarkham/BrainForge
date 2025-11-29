"""Ingestion service for BrainForge content processing pipeline."""

import asyncio
import hashlib
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ingestion import (
    ContentType, IngestionTask, IngestionTaskCreate, IngestionTaskUpdate, ProcessingState
)
from src.models.content_source import ContentSource, ContentSourceCreate
from src.models.processing_result import ProcessingResult, ProcessingResultCreate
from src.models.pdf_metadata import PDFMetadata, PDFMetadataCreate
from src.models.pdf_processing_result import PDFProcessingResult, PDFProcessingResultCreate
from src.models.review_queue import ReviewQueue, ReviewQueueCreate, ReviewStatus
from src.models.audit_trail import AuditTrail, AuditTrailCreate
from src.models.note import Note, NoteCreate, NoteType
from src.services.base import BaseService
from src.services.pdf_processor import PDFProcessor
from src.services.embedding_generator import EmbeddingGenerator
from src.services.semantic_search import SemanticSearchService
from src.services.database import DatabaseService
from src.services.vector_store import VectorStore
from src.services.hnsw_index import HNSWIndex

logger = logging.getLogger(__name__)


class IngestionService:
    """Ingestion service for processing external content into the knowledge base."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.database_service = DatabaseService()
        self.pdf_processor = PDFProcessor()
        self.embedding_generator = EmbeddingGenerator(self.database_service)
        
        # Initialize semantic search dependencies
        self.vector_store = VectorStore(database_url)
        self.hnsw_index = HNSWIndex(database_url)
        self.semantic_search = SemanticSearchService(
            self.embedding_generator,
            self.vector_store,
            self.hnsw_index,
            self.database_service
        )
        
        # Initialize database services
        self.ingestion_task_service = BaseService(IngestionTask)
        self.content_source_service = BaseService(ContentSource)
        self.processing_result_service = BaseService(ProcessingResult)
        self.pdf_metadata_service = BaseService(PDFMetadata)
        self.pdf_processing_result_service = BaseService(PDFProcessingResult)
        self.review_queue_service = BaseService(ReviewQueue)
        self.audit_trail_service = BaseService(AuditTrail)
        self.note_service = BaseService(Note)
    
    async def create_ingestion_task(
        self,
        content_type: ContentType,
        source_url: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        tags: List[str] = None,
        priority: str = "normal",
        created_by: str = "system"
    ) -> IngestionTask:
        """Create a new ingestion task."""
        if tags is None:
            tags = []
        
        task_data = IngestionTaskCreate(
            content_type=content_type,
            source_url=source_url,
            file_name=file_name,
            file_size=file_size,
            tags=tags,
            priority=priority,
            created_by=created_by,
            provenance={"created_by": created_by, "timestamp": datetime.now().isoformat()}
        )
        
        # Estimate completion time based on content type and priority
        base_time = 2 if content_type == ContentType.PDF else 1  # minutes
        if priority == "high":
            base_time *= 0.5
        elif priority == "low":
            base_time *= 2
        
        task_data.estimated_completion = datetime.now() + timedelta(minutes=base_time)
        
        async with AsyncSession() as session:
            task = await self.ingestion_task_service.create(session, task_data)
            await self._log_audit_trail(
                session, task.id, "task_created", 
                f"Ingestion task created for {content_type.value}", created_by
            )
            return task
    
    async def process_pdf_task(self, task_id: UUID, file_path: str) -> Dict[str, Any]:
        """Process a PDF ingestion task through the full pipeline."""
        async with AsyncSession() as session:
            try:
                # Get the task
                task = await self.ingestion_task_service.get(session, task_id)
                if not task:
                    raise ValueError(f"Ingestion task not found: {task_id}")
                
                # Update task state
                await self._update_task_state(session, task_id, ProcessingState.VALIDATING)
                
                # Step 1: Validate PDF
                validation_result = await self.pdf_processor.validate_pdf(file_path)
                if not validation_result.get("is_valid", False):
                    await self._update_task_state(session, task_id, ProcessingState.FAILED)
                    await self._log_audit_trail(
                        session, task_id, "validation_failed",
                        f"PDF validation failed: {validation_result.get('validation_notes', 'Unknown error')}",
                        "system"
                    )
                    return {"success": False, "error": "PDF validation failed"}
                
                # Step 2: Extract metadata and text
                await self._update_task_state(session, task_id, ProcessingState.EXTRACTING_METADATA)
                processing_result = await self.pdf_processor.process_pdf(file_path)
                
                if not processing_result.get("success", False):
                    await self._update_task_state(session, task_id, ProcessingState.FAILED)
                    await self._log_audit_trail(
                        session, task_id, "extraction_failed",
                        f"PDF extraction failed: {processing_result.get('error', 'Unknown error')}",
                        "system"
                    )
                    return processing_result
                
                # Step 3: Store processing results
                await self._update_task_state(session, task_id, ProcessingState.ASSESSING_QUALITY)
                
                # Create content source
                content_hash = self._calculate_content_hash(file_path)
                content_source_data = ContentSourceCreate(
                    ingestion_task_id=task_id,
                    source_type="pdf",
                    source_url=task.source_url,
                    source_metadata=processing_result["metadata"],
                    retrieval_method="file_upload",
                    retrieval_timestamp=datetime.now(),
                    content_hash=content_hash,
                    created_by="system"
                )
                content_source = await self.content_source_service.create(session, content_source_data)
                
                # Create PDF metadata
                pdf_metadata_data = PDFMetadataCreate(
                    ingestion_task_id=task_id,
                    page_count=processing_result["metadata"].get("page_count", 0),
                    author=processing_result["metadata"].get("author"),
                    title=processing_result["metadata"].get("title"),
                    subject=processing_result["metadata"].get("subject"),
                    creation_date=processing_result["metadata"].get("creation_date"),
                    modification_date=processing_result["metadata"].get("modification_date"),
                    pdf_version=processing_result["metadata"].get("pdf_version", "unknown"),
                    encryption_status=processing_result["metadata"].get("encryption_status", "none"),
                    extraction_method=processing_result["metadata"].get("extraction_method", "unknown"),
                    extraction_quality_score=processing_result["text_result"].get("quality_score", 0.0),
                    created_by="system"
                )
                pdf_metadata = await self.pdf_metadata_service.create(session, pdf_metadata_data)
                
                # Create PDF processing result
                pdf_processing_data = PDFProcessingResultCreate(
                    ingestion_task_id=task_id,
                    extracted_text=processing_result["text_result"].get("extracted_text", ""),
                    text_quality_metrics={
                        "character_count": processing_result["text_result"].get("character_count", 0),
                        "word_count": processing_result["text_result"].get("word_count", 0),
                        "extraction_confidence": processing_result["text_result"].get("quality_score", 0.0)
                    },
                    section_breaks={},  # Would be populated by advanced processing
                    processing_time_ms=processing_result["text_result"].get("processing_time_ms", 0),
                    dockling_version=processing_result["text_result"].get("dockling_version", "none"),
                    created_by="system"
                )
                pdf_processing_result = await self.pdf_processing_result_service.create(session, pdf_processing_data)
                
                # Step 4: Generate summary and classifications
                await self._update_task_state(session, task_id, ProcessingState.SUMMARIZING)
                summary, classifications = await self._generate_summary_and_classifications(
                    processing_result["text_result"].get("extracted_text", "")
                )
                
                # Step 5: Create processing result
                processing_result_data = ProcessingResultCreate(
                    ingestion_task_id=task_id,
                    summary=summary,
                    classifications=classifications,
                    connection_suggestions=[],  # Would be populated by semantic search
                    confidence_scores={
                        "extraction_quality": processing_result["text_result"].get("quality_score", 0.0),
                        "summary_confidence": 0.8,  # Placeholder
                        "classification_confidence": 0.7  # Placeholder
                    },
                    processing_metadata=processing_result,
                    created_by="system"
                )
                processing_result_entity = await self.processing_result_service.create(session, processing_result_data)
                
                # Step 6: Add to review queue if quality is low
                quality_score = processing_result["text_result"].get("quality_score", 0.0)
                if quality_score < 0.7:
                    await self._update_task_state(session, task_id, ProcessingState.AWAITING_REVIEW)
                    review_queue_data = ReviewQueueCreate(
                        ingestion_task_id=task_id,
                        review_status=ReviewStatus.PENDING,
                        priority=1 if task.priority == "high" else 0,
                        created_by="system"
                    )
                    await self.review_queue_service.create(session, review_queue_data)
                else:
                    # Auto-approve high-quality content
                    await self._integrate_content(session, task_id, processing_result_entity)
                    await self._update_task_state(session, task_id, ProcessingState.INTEGRATED)
                
                await self._log_audit_trail(
                    session, task_id, "processing_completed",
                    f"PDF processing completed successfully (quality: {quality_score:.2f})",
                    "system"
                )
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "content_source_id": content_source.id,
                    "pdf_metadata_id": pdf_metadata.id,
                    "processing_result_id": processing_result_entity.id,
                    "quality_score": quality_score,
                    "requires_review": quality_score < 0.7
                }
                
            except Exception as e:
                logger.error(f"PDF processing failed for task {task_id}: {e}")
                await self._update_task_state(session, task_id, ProcessingState.FAILED)
                await self._log_audit_trail(
                    session, task_id, "processing_failed",
                    f"PDF processing failed: {str(e)}",
                    "system"
                )
                return {"success": False, "error": str(e)}
    
    async def _update_task_state(self, session: AsyncSession, task_id: UUID, state: ProcessingState):
        """Update ingestion task state."""
        update_data = IngestionTaskUpdate(processing_state=state)
        await self.ingestion_task_service.update(session, task_id, update_data)
    
    async def _log_audit_trail(
        self, session: AsyncSession, task_id: UUID, action_type: str, 
        action_details: str, performed_by: str
    ):
        """Log an audit trail entry."""
        audit_data = AuditTrailCreate(
            ingestion_task_id=task_id,
            action_type=action_type,
            action_details={"description": action_details},
            performed_by=performed_by,
            outcome="success",
            created_by=performed_by
        )
        await self.audit_trail_service.create(session, audit_data)
    
    async def _generate_summary_and_classifications(self, text: str) -> tuple[str, List[str]]:
        """Generate summary and classifications for extracted text."""
        # Placeholder implementation - would integrate with AI services
        summary = f"Extracted {len(text)} characters from PDF content."
        
        # Basic classification based on text content
        classifications = []
        if len(text) > 1000:
            classifications.append("long_content")
        if "research" in text.lower():
            classifications.append("research")
        if "technical" in text.lower():
            classifications.append("technical")
        
        return summary, classifications
    
    async def _integrate_content(self, session: AsyncSession, task_id: UUID, processing_result: ProcessingResult):
        """Integrate processed content into the knowledge base as a note."""
        # Create a literature note from the processed content
        note_data = NoteCreate(
            content=f"# {processing_result.summary}\n\n{processing_result.processing_metadata.get('text_result', {}).get('extracted_text', '')}",
            note_type=NoteType.LITERATURE,
            metadata={
                "source_type": "pdf",
                "processing_result_id": str(processing_result.id),
                "classifications": processing_result.classifications,
                "confidence_scores": processing_result.confidence_scores
            },
            created_by="system",
            is_ai_generated=True,
            ai_justification="Content automatically processed from PDF ingestion"
        )
        
        note = await self.note_service.create(session, note_data)
        
        # Generate embedding for semantic search
        await self.embedding_generator.generate_embedding(note.id, note.content)
        
        logger.info(f"Content integrated as note {note.id} for task {task_id}")
    
    def _calculate_content_hash(self, file_path: str) -> str:
        """Calculate content hash for deduplication."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    async def get_task_status(self, task_id: UUID) -> Dict[str, Any]:
        """Get current status of an ingestion task."""
        async with AsyncSession() as session:
            task = await self.ingestion_task_service.get(session, task_id)
            if not task:
                return {"error": "Task not found"}
            
            return {
                "task_id": task_id,
                "status": task.processing_state.value,
                "progress": self._calculate_progress(task.processing_state),
                "estimated_completion": task.estimated_completion,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
    
    def _calculate_progress(self, state: ProcessingState) -> int:
        """Calculate progress percentage based on processing state."""
        progress_map = {
            ProcessingState.VALIDATING: 10,
            ProcessingState.EXTRACTING_METADATA: 30,
            ProcessingState.EXTRACTING_TEXT: 50,
            ProcessingState.ASSESSING_QUALITY: 70,
            ProcessingState.SUMMARIZING: 80,
            ProcessingState.CLASSIFYING: 90,
            ProcessingState.AWAITING_REVIEW: 95,
            ProcessingState.INTEGRATED: 100,
            ProcessingState.FAILED: 0
        }
        return progress_map.get(state, 0)