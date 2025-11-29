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
    "SearchHealth"
]