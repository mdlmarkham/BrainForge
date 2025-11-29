"""Quality Assessment model for evaluating content credibility and relevance."""

from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class QualityScoreType:
    """Quality score type constants."""
    CREDIBILITY = "credibility"
    RELEVANCE = "relevance"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    OVERALL = "overall"


class QualityAssessment(BaseEntity):
    """Represents multi-factor evaluation of content credibility, relevance, and quality."""
    
    content_source_id: UUID = Field(..., description="ID of the content source being assessed")
    score_type: str = Field(..., description="Type of quality score")
    score_value: float = Field(..., ge=0.0, le=1.0, description="Score value between 0 and 1")
    score_rationale: str = Field(..., description="Rationale for the score")
    confidence_level: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the assessment")
    assessment_metadata: dict[str, str] = Field(default_factory=dict, description="Metadata about the assessment")


class QualityAssessmentCreate(BaseEntity):
    """Create schema for quality assessments."""
    
    content_source_id: UUID = Field(..., description="ID of the content source being assessed")
    score_type: str = Field(..., description="Type of quality score")
    score_value: float = Field(..., ge=0.0, le=1.0, description="Score value between 0 and 1")
    score_rationale: str = Field(..., description="Rationale for the score")
    confidence_level: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the assessment")
    assessment_metadata: dict[str, str] = Field(default_factory=dict, description="Metadata about the assessment")


class QualityScore(BaseEntity):
    """Individual quality score component."""
    
    score_type: str = Field(..., description="Type of quality score")
    score_value: float = Field(..., ge=0.0, le=1.0, description="Score value between 0 and 1")
    score_rationale: str = Field(..., description="Rationale for the score")
    confidence_level: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the score")


class QualityAssessmentUpdate(BaseEntity):
    """Update schema for quality assessments."""
    
    score_type: Optional[str] = Field(default=None, description="Type of quality score")
    score_value: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Score value between 0 and 1")
    score_rationale: Optional[str] = Field(default=None, description="Rationale for the score")
    confidence_level: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence in the assessment")
    assessment_metadata: Optional[dict[str, str]] = Field(default=None, description="Metadata about the assessment")