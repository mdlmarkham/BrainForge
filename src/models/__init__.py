"""BrainForge AI Knowledge Base - Data models package."""

from .agent_run import AgentRun, AgentRunCreate
from .audit_trail import AuditTrail, AuditTrailCreate, AuditTrailUpdate
from .base import AIGeneratedMixin, BaseEntity, ProvenanceMixin, VersionMixin
from .content_source import (
    ContentSource,
    ContentSourceCreate,
    ContentSourceType,
    ContentSourceUpdate,
)
from .embedding import Embedding, EmbeddingCreate
from .ingestion import (
    ContentType,
    IngestionTask,
    IngestionTaskCreate,
    IngestionTaskUpdate,
    ProcessingState,
)
from .integration_proposal import (
    IntegrationProposal,
    IntegrationProposalCreate,
    IntegrationProposalStatus,
    IntegrationProposalUpdate,
)
from .link import Link, LinkCreate
from .mcp_execution import (
    MCPToolExecution,
    MCPToolExecutionCreate,
    MCPToolExecutionUpdate,
)
from .mcp_session import MCPSession, MCPSessionCreate, MCPSessionUpdate
from .mcp_tool import MCPTool, MCPToolCreate, MCPToolUpdate
from .mcp_workflow import MCPWorkflow, MCPWorkflowCreate, MCPWorkflowUpdate
from .note import Note, NoteCreate, NoteType, NoteUpdate
from .pdf_metadata import PDFMetadata, PDFMetadataCreate, PDFMetadataUpdate
from .pdf_processing_result import (
    PDFProcessingResult,
    PDFProcessingResultCreate,
    PDFProcessingResultUpdate,
)
from .processing_result import (
    ProcessingResult,
    ProcessingResultCreate,
    ProcessingResultUpdate,
)
from .quality_assessment import (
    QualityAssessment,
    QualityAssessmentCreate,
    QualityAssessmentUpdate,
    QualityScoreType,
)
from .research_audit_trail import (
    AuditActionType,
    ResearchAuditTrail,
    ResearchAuditTrailCreate,
    ResearchAuditTrailUpdate,
)
from .research_review_queue import (
    ResearchReviewQueue,
    ResearchReviewQueueCreate,
    ResearchReviewQueueUpdate,
)
from .research_run import (
    ResearchRun,
    ResearchRunCreate,
    ResearchRunStatus,
    ResearchRunUpdate,
)
from .review_queue import (
    ReviewQueue,
    ReviewQueueCreate,
    ReviewQueueUpdate,
    ReviewStatus,
)
from .search import (
    SearchHealth,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchStats,
)
from .version_history import VersionHistory, VersionHistoryCreate

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
    "AuditActionType",
    "MCPTool",
    "MCPToolCreate",
    "MCPToolUpdate",
    "MCPSession",
    "MCPSessionCreate",
    "MCPSessionUpdate",
    "MCPToolExecution",
    "MCPToolExecutionCreate",
    "MCPToolExecutionUpdate",
    "MCPWorkflow",
    "MCPWorkflowCreate",
    "MCPWorkflowUpdate"
]
