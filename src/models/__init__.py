"""BrainForge AI Knowledge Base - Data models package."""

from .base import BaseEntity, AIGeneratedMixin, ProvenanceMixin, VersionMixin
from .note import Note, NoteCreate, NoteUpdate, NoteType
from .embedding import Embedding, EmbeddingCreate
from .link import Link, LinkCreate
from .agent_run import AgentRun, AgentRunCreate
from .version_history import VersionHistory, VersionHistoryCreate
from .search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchStats,
    SearchHealth
)
from .ingestion import IngestionTask, IngestionTaskCreate, IngestionTaskUpdate, ContentType, ProcessingState
from .content_source import ContentSource, ContentSourceCreate, ContentSourceUpdate
from .processing_result import ProcessingResult, ProcessingResultCreate, ProcessingResultUpdate
from .pdf_metadata import PDFMetadata, PDFMetadataCreate, PDFMetadataUpdate
from .pdf_processing_result import PDFProcessingResult, PDFProcessingResultCreate, PDFProcessingResultUpdate
from .review_queue import ReviewQueue, ReviewQueueCreate, ReviewQueueUpdate, ReviewStatus
from .audit_trail import AuditTrail, AuditTrailCreate, AuditTrailUpdate
from .research_run import ResearchRun, ResearchRunCreate, ResearchRunUpdate, ResearchRunStatus
from .content_source import ContentSource, ContentSourceCreate, ContentSourceUpdate, ContentSourceType
from .quality_assessment import QualityAssessment, QualityAssessmentCreate, QualityAssessmentUpdate, QualityScoreType
from .research_review_queue import ResearchReviewQueue, ResearchReviewQueueCreate, ResearchReviewQueueUpdate
from .integration_proposal import IntegrationProposal, IntegrationProposalCreate, IntegrationProposalUpdate, IntegrationProposalStatus
from .research_audit_trail import ResearchAuditTrail, ResearchAuditTrailCreate, ResearchAuditTrailUpdate, AuditActionType

__all__ = [
    "BaseEntity",
    "AIGeneratedMixin",
    "ProvenanceMixin",
    "VersionMixin",
    "Note",
    "NoteCreate",
    "NoteUpdate",
    "NoteType",
    "Embedding",
    "EmbeddingCreate",
    "Link",
    "LinkCreate",
    "AgentRun",
    "AgentRunCreate",
    "VersionHistory",
    "VersionHistoryCreate",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "SearchStats",
    "SearchHealth",
    "IngestionTask",
    "IngestionTaskCreate",
    "IngestionTaskUpdate",
    "ContentType",
    "ProcessingState",
    "ContentSource",
    "ContentSourceCreate",
    "ContentSourceUpdate",
    "ProcessingResult",
    "ProcessingResultCreate",
    "ProcessingResultUpdate",
    "PDFMetadata",
    "PDFMetadataCreate",
    "PDFMetadataUpdate",
    "PDFProcessingResult",
    "PDFProcessingResultCreate",
    "PDFProcessingResultUpdate",
    "ReviewQueue",
    "ReviewQueueCreate",
    "ReviewQueueUpdate",
    "ReviewStatus",
    "AuditTrail",
    "AuditTrailCreate",
    "AuditTrailUpdate",
    "ResearchRun",
    "ResearchRunCreate",
    "ResearchRunUpdate",
    "ResearchRunStatus",
    "ContentSource",
    "ContentSourceCreate",
    "ContentSourceUpdate",
    "ContentSourceType",
    "QualityAssessment",
    "QualityAssessmentCreate",
    "QualityAssessmentUpdate",
    "QualityScoreType",
    "ResearchReviewQueue",
    "ResearchReviewQueueCreate",
    "ResearchReviewQueueUpdate",
    "IntegrationProposal",
    "IntegrationProposalCreate",
    "IntegrationProposalUpdate",
    "IntegrationProposalStatus",
    "ResearchAuditTrail",
    "ResearchAuditTrailCreate",
    "ResearchAuditTrailUpdate",
    "AuditActionType"
]