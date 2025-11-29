"""Freshness scoring service for evaluating content timeliness and recency."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ...models.content_source import ContentSource

logger = logging.getLogger(__name__)


class FreshnessScorer:
    """Scores content freshness based on publication date, update frequency, and temporal relevance."""
    
    def __init__(self):
        # Freshness scoring thresholds (in days)
        self.freshness_thresholds = {
            "very_fresh": 7,      # Within a week
            "fresh": 30,          # Within a month
            "recent": 90,         # Within 3 months
            "somewhat_recent": 180,  # Within 6 months
            "aging": 365,         # Within a year
            "old": 730,           # Within 2 years
            "very_old": 1825,     # Within 5 years
        }
        
        # Topic-specific freshness requirements (in days)
        self.topic_freshness_requirements = {
            "technology": 180,     # Tech content should be recent
            "science": 365,        # Science can be older but not ancient
            "news": 7,            # News should be very fresh
            "politics": 30,       # Politics should be current
            "health": 90,         # Health information should be recent
            "finance": 30,        # Financial info should be current
            "education": 365,     # Educational content can be older
            "history": 1825,      # Historical content can be much older
        }
    
    async def score_content(self, content_source: ContentSource, research_topic: str = None) -> float:
        """Score content freshness on a scale of 0.0 to 1.0."""
        
        try:
            # Get publication date from content source
            publication_date = self._extract_publication_date(content_source)
            
            if not publication_date:
                logger.warning(f"No publication date found for {content_source.url}")
                return 0.5  # Neutral score for unknown dates
            
            # Calculate age in days
            age_days = self._calculate_age_days(publication_date)
            
            # Determine topic-specific freshness requirement
            freshness_requirement = self._get_freshness_requirement(research_topic)
            
            # Calculate freshness score based on age and requirement
            freshness_score = self._calculate_freshness_score(age_days, freshness_requirement)
            
            # Apply recency bonuses for very fresh content
            if age_days <= self.freshness_thresholds["very_fresh"]:
                freshness_score = min(1.0, freshness_score + 0.1)
            
            # Apply penalties for very old content
            if age_days > self.freshness_thresholds["very_old"]:
                freshness_score = max(0.1, freshness_score - 0.2)
            
            logger.debug(f"Freshness scoring for {content_source.url}: "
                        f"age={age_days}d, requirement={freshness_requirement}d, "
                        f"score={freshness_score:.2f}")
            
            return round(freshness_score, 2)
            
        except Exception as e:
            logger.error(f"Error scoring freshness for {content_source.url}: {e}")
            return 0.5  # Default neutral score on error
    
    def _extract_publication_date(self, content_source: ContentSource) -> Optional[datetime]:
        """Extract publication date from content source metadata."""
        
        # Check for explicit publication date
        if hasattr(content_source, 'publication_date') and content_source.publication_date:
            return content_source.publication_date
        
        # Check metadata for date information
        if hasattr(content_source, 'metadata') and content_source.metadata:
            metadata = content_source.metadata
            
            # Common date field names in metadata
            date_fields = [
                'publication_date', 'published_date', 'date_published',
                'created_date', 'date_created', 'timestamp',
                'last_modified', 'updated_date', 'date'
            ]
            
            for field in date_fields:
                if (isinstance(metadata, dict) and 
                    field in metadata and 
                    metadata[field]):
                    try:
                        date_str = str(metadata[field])
                        return self._parse_date(date_str)
                    except (ValueError, TypeError):
                        continue
        
        # Check if content source has a created_at field
        if hasattr(content_source, 'created_at') and content_source.created_at:
            return content_source.created_at
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object."""
        
        try:
            # Try common date formats
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%B %d, %Y",
                "%d %B %Y",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If none of the formats work, try parsing as ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
        except (ValueError, TypeError):
            logger.warning(f"Could not parse date string: {date_str}")
            return None
    
    def _calculate_age_days(self, publication_date: datetime) -> int:
        """Calculate age of content in days."""
        
        current_date = datetime.now()
        age_delta = current_date - publication_date
        return age_delta.days
    
    def _get_freshness_requirement(self, research_topic: str) -> int:
        """Get freshness requirement in days based on research topic."""
        
        if not research_topic:
            return self.freshness_thresholds["recent"]  # Default requirement
        
        research_topic_lower = research_topic.lower()
        
        # Match topic to freshness requirements
        for topic, requirement in self.topic_freshness_requirements.items():
            if topic in research_topic_lower:
                return requirement
        
        # Check for topic keywords that indicate specific freshness needs
        if any(keyword in research_topic_lower for keyword in ["news", "current", "recent", "today"]):
            return self.topic_freshness_requirements["news"]
        
        if any(keyword in research_topic_lower for keyword in ["technology", "tech", "software", "ai"]):
            return self.topic_freshness_requirements["technology"]
        
        if any(keyword in research_topic_lower for keyword in ["science", "research", "study"]):
            return self.topic_freshness_requirements["science"]
        
        if any(keyword in research_topic_lower for keyword in ["politics", "government", "policy"]):
            return self.topic_freshness_requirements["politics"]
        
        if any(keyword in research_topic_lower for keyword in ["health", "medical", "medicine"]):
            return self.topic_freshness_requirements["health"]
        
        if any(keyword in research_topic_lower for keyword in ["finance", "economic", "market"]):
            return self.topic_freshness_requirements["finance"]
        
        # Default requirement for unknown topics
        return self.freshness_thresholds["recent"]
    
    def _calculate_freshness_score(self, age_days: int, freshness_requirement: int) -> float:
        """Calculate freshness score based on age and requirement."""
        
        if age_days <= 0:
            return 1.0  # Future or current date - maximum freshness
        
        # Calculate score using exponential decay
        # Score decays faster as content ages beyond requirement
        if age_days <= freshness_requirement:
            # Within requirement - high score with linear decay
            ratio = age_days / freshness_requirement
            score = 1.0 - (ratio * 0.3)  # Only lose 30% at requirement boundary
        else:
            # Beyond requirement - exponential decay
            excess_days = age_days - freshness_requirement
            decay_factor = min(0.9, excess_days / (freshness_requirement * 2))
            score = 0.7 * (1.0 - decay_factor)  # Start from 0.7 and decay
        
        return max(0.1, min(1.0, score))
    
    async def get_freshness_analysis(self, content_source: ContentSource, research_topic: str = None) -> Dict[str, Any]:
        """Get detailed freshness analysis for content."""
        
        publication_date = self._extract_publication_date(content_source)
        age_days = self._calculate_age_days(publication_date) if publication_date else None
        freshness_requirement = self._get_freshness_requirement(research_topic)
        freshness_score = await self.score_content(content_source, research_topic)
        
        # Determine freshness category
        freshness_category = self._get_freshness_category(age_days) if age_days else "unknown"
        
        return {
            "freshness_score": freshness_score,
            "publication_date": publication_date.isoformat() if publication_date else None,
            "age_days": age_days,
            "freshness_requirement_days": freshness_requirement,
            "freshness_category": freshness_category,
            "within_requirement": age_days <= freshness_requirement if age_days else None,
            "research_topic": research_topic,
            "content_source_id": str(content_source.id) if hasattr(content_source, 'id') else None
        }
    
    def _get_freshness_category(self, age_days: int) -> str:
        """Get human-readable freshness category."""
        
        if age_days <= self.freshness_thresholds["very_fresh"]:
            return "very_fresh"
        elif age_days <= self.freshness_thresholds["fresh"]:
            return "fresh"
        elif age_days <= self.freshness_thresholds["recent"]:
            return "recent"
        elif age_days <= self.freshness_thresholds["somewhat_recent"]:
            return "somewhat_recent"
        elif age_days <= self.freshness_thresholds["aging"]:
            return "aging"
        elif age_days <= self.freshness_thresholds["old"]:
            return "old"
        else:
            return "very_old"
    
    async def score_multiple_contents(self, content_sources: list, research_topic: str = None) -> Dict[str, Any]:
        """Score freshness for multiple content sources and provide comparative analysis."""
        
        scores = []
        analyses = []
        
        for content_source in content_sources:
            score = await self.score_content(content_source, research_topic)
            analysis = await self.get_freshness_analysis(content_source, research_topic)
            
            scores.append(score)
            analyses.append(analysis)
        
        # Calculate statistics
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
        else:
            avg_score = max_score = min_score = 0.0
        
        return {
            "scores": scores,
            "analyses": analyses,
            "statistics": {
                "average_score": round(avg_score, 2),
                "max_score": round(max_score, 2),
                "min_score": round(min_score, 2),
                "count": len(scores)
            },
            "research_topic": research_topic
        }
    
    def update_freshness_thresholds(self, new_thresholds: Dict[str, int]) -> None:
        """Update freshness scoring thresholds."""
        
        self.freshness_thresholds.update(new_thresholds)
        logger.info(f"Updated freshness thresholds: {new_thresholds}")
    
    def update_topic_requirements(self, new_requirements: Dict[str, int]) -> None:
        """Update topic-specific freshness requirements."""
        
        self.topic_freshness_requirements.update(new_requirements)
        logger.info(f"Updated topic freshness requirements: {new_requirements}")