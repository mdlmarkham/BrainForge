"""Completeness scoring service for evaluating content depth and comprehensiveness."""

import logging
import re
from typing import Dict, Any, List

from ...models.content_source import ContentSource

logger = logging.getLogger(__name__)


class CompletenessScorer:
    """Scores content completeness based on depth, coverage, and structural indicators."""
    
    def __init__(self):
        # Completeness indicators and their weights
        self.completeness_indicators = {
            "length_indicator": 0.2,
            "structural_elements": 0.3,
            "reference_presence": 0.25,
            "multimedia_elements": 0.15,
            "methodology_presence": 0.1,
        }
        
        # Structural elements that indicate comprehensive content
        self.structural_elements = [
            "introduction", "background", "method", "methodology", "results",
            "findings", "discussion", "conclusion", "summary", "abstract",
            "references", "bibliography", "acknowledgments", "appendix"
        ]
        
        # Reference patterns
        self.reference_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\(\w+ et al\.',  # (Smith et al.
            r'\bdoi:',  # doi:10.1234/abc
            r'\barXiv:',  # arXiv:1234.5678
            r'\bhttp[s]?://',  # URLs
        ]
        
        # Multimedia element indicators
        self.multimedia_indicators = [
            "figure", "table", "chart", "graph", "image", "diagram",
            "illustration", "photo", "video", "audio"
        ]
    
    async def score_content(self, content_source: ContentSource) -> float:
        """Score content completeness on a scale of 0.0 to 1.0."""
        
        try:
            scores = []
            weights = []
            
            # 1. Length-based scoring
            length_score = self._score_content_length(content_source)
            scores.append(length_score)
            weights.append(self.completeness_indicators["length_indicator"])
            
            # 2. Structural elements scoring
            structure_score = self._score_structural_elements(content_source)
            scores.append(structure_score)
            weights.append(self.completeness_indicators["structural_elements"])
            
            # 3. Reference presence scoring
            reference_score = self._score_reference_presence(content_source)
            scores.append(reference_score)
            weights.append(self.completeness_indicators["reference_presence"])
            
            # 4. Multimedia elements scoring
            multimedia_score = self._score_multimedia_elements(content_source)
            scores.append(multimedia_score)
            weights.append(self.completeness_indicators["multimedia_elements"])
            
            # 5. Methodology presence scoring
            methodology_score = self._score_methodology_presence(content_source)
            scores.append(methodology_score)
            weights.append(self.completeness_indicators["methodology_presence"])
            
            # Calculate weighted average
            weighted_score = sum(score * weight for score, weight in zip(scores, weights))
            weighted_score = max(0.0, min(1.0, weighted_score))  # Clamp to 0-1 range
            
            logger.debug(f"Completeness scoring for {content_source.url}: "
                        f"length={length_score:.2f}, structure={structure_score:.2f}, "
                        f"references={reference_score:.2f}, multimedia={multimedia_score:.2f}, "
                        f"methodology={methodology_score:.2f}, final={weighted_score:.2f}")
            
            return round(weighted_score, 2)
            
        except Exception as e:
            logger.error(f"Error scoring completeness for {content_source.url}: {e}")
            return 0.5  # Default neutral score on error
    
    def _score_content_length(self, content_source: ContentSource) -> float:
        """Score based on content length and word count."""
        
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        word_count = len(content_text.split())
        
        # Score based on word count ranges
        if word_count >= 2000:
            return 1.0  # Very comprehensive
        elif word_count >= 1000:
            return 0.8  # Comprehensive
        elif word_count >= 500:
            return 0.6  # Moderate length
        elif word_count >= 200:
            return 0.4  # Short but substantive
        elif word_count >= 100:
            return 0.3  # Brief
        else:
            return 0.2  # Very brief
    
    def _score_structural_elements(self, content_source: ContentSource) -> float:
        """Score based on presence of structural elements indicating comprehensive content."""
        
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        content_lower = content_text.lower()
        
        # Count structural elements present
        elements_present = 0
        for element in self.structural_elements:
            if element in content_lower:
                elements_present += 1
        
        # Calculate score based on element count
        total_elements = len(self.structural_elements)
        element_ratio = elements_present / total_elements
        
        # Apply non-linear scaling (more elements = exponentially better)
        if element_ratio == 0:
            score = 0.1
        elif element_ratio < 0.3:
            score = 0.3 + (element_ratio * 0.4)
        elif element_ratio < 0.6:
            score = 0.5 + ((element_ratio - 0.3) * 0.4)
        else:
            score = 0.7 + ((element_ratio - 0.6) * 0.3)
        
        return max(0.0, min(1.0, score))
    
    def _score_reference_presence(self, content_source: ContentSource) -> float:
        """Score based on presence of references and citations."""
        
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        # Count reference patterns
        reference_count = 0
        for pattern in self.reference_patterns:
            matches = re.findall(pattern, content_text)
            reference_count += len(matches)
        
        # Score based on reference count
        if reference_count >= 10:
            return 1.0  # Well-referenced
        elif reference_count >= 5:
            return 0.8  # Adequately referenced
        elif reference_count >= 3:
            return 0.6  # Some references
        elif reference_count >= 1:
            return 0.4  # Minimal references
        else:
            return 0.2  # No references
    
    def _score_multimedia_elements(self, content_source: ContentSource) -> float:
        """Score based on presence of multimedia elements."""
        
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        content_lower = content_text.lower()
        
        # Count multimedia indicators
        multimedia_count = 0
        for indicator in self.multimedia_indicators:
            if indicator in content_lower:
                multimedia_count += 1
        
        # Also check metadata for multimedia indicators
        if hasattr(content_source, 'metadata') and content_source.metadata:
            metadata_str = str(content_source.metadata).lower()
            for indicator in self.multimedia_indicators:
                if indicator in metadata_str and indicator not in content_lower:
                    multimedia_count += 1
        
        # Score based on multimedia count
        if multimedia_count >= 3:
            return 0.8  # Rich multimedia content
        elif multimedia_count >= 2:
            return 0.6  # Some multimedia
        elif multimedia_count >= 1:
            return 0.4  # Minimal multimedia
        else:
            return 0.2  # No multimedia
    
    def _score_methodology_presence(self, content_source: ContentSource) -> float:
        """Score based on presence of methodology description."""
        
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        content_lower = content_text.lower()
        
        # Methodology indicators
        methodology_indicators = [
            "method", "methodology", "approach", "procedure", "technique",
            "experiment", "study design", "research design", "data collection",
            "analysis method", "statistical analysis"
        ]
        
        methodology_present = False
        methodology_depth = 0
        
        for indicator in methodology_indicators:
            if indicator in content_lower:
                methodology_present = True
                # Check for depth by looking for methodology context
                if any(context in content_lower for context in ["detailed", "comprehensive", "thorough"]):
                    methodology_depth += 2
                elif any(context in content_lower for context in ["brief", "summary", "overview"]):
                    methodology_depth += 1
                else:
                    methodology_depth += 1
        
        if methodology_present:
            if methodology_depth >= 3:
                return 0.9  # Detailed methodology
            elif methodology_depth >= 2:
                return 0.7  # Good methodology description
            else:
                return 0.5  # Basic methodology mention
        else:
            return 0.2  # No methodology
    
    def _get_content_text(self, content_source: ContentSource) -> str:
        """Extract combined text from content source for analysis."""
        
        text_parts = []
        
        # Add title if available
        if content_source.title:
            text_parts.append(content_source.title)
        
        # Add description if available
        if content_source.description:
            text_parts.append(content_source.description)
        
        # Add content if available
        if hasattr(content_source, 'content') and content_source.content:
            text_parts.append(content_source.content)
        
        # Add metadata as string if available
        if hasattr(content_source, 'metadata') and content_source.metadata:
            text_parts.append(str(content_source.metadata))
        
        return " ".join(text_parts)
    
    async def get_completeness_breakdown(self, content_source: ContentSource) -> Dict[str, Any]:
        """Get detailed completeness scoring breakdown."""
        
        length_score = self._score_content_length(content_source)
        structure_score = self._score_structural_elements(content_source)
        reference_score = self._score_reference_presence(content_source)
        multimedia_score = self._score_multimedia_elements(content_source)
        methodology_score = self._score_methodology_presence(content_source)
        
        overall_score = await self.score_content(content_source)
        
        return {
            "overall_score": overall_score,
            "breakdown": {
                "content_length": {
                    "score": length_score,
                    "weight": self.completeness_indicators["length_indicator"],
                    "contribution": length_score * self.completeness_indicators["length_indicator"]
                },
                "structural_elements": {
                    "score": structure_score,
                    "weight": self.completeness_indicators["structural_elements"],
                    "contribution": structure_score * self.completeness_indicators["structural_elements"]
                },
                "reference_presence": {
                    "score": reference_score,
                    "weight": self.completeness_indicators["reference_presence"],
                    "contribution": reference_score * self.completeness_indicators["reference_presence"]
                },
                "multimedia_elements": {
                    "score": multimedia_score,
                    "weight": self.completeness_indicators["multimedia_elements"],
                    "contribution": multimedia_score * self.completeness_indicators["multimedia_elements"]
                },
                "methodology_presence": {
                    "score": methodology_score,
                    "weight": self.completeness_indicators["methodology_presence"],
                    "contribution": methodology_score * self.completeness_indicators["methodology_presence"]
                }
            },
            "content_source_id": str(content_source.id) if hasattr(content_source, 'id') else None
        }
    
    def update_completeness_weights(self, new_weights: Dict[str, float]) -> None:
        """Update completeness scoring weights."""
        
        # Validate that weights sum to 1.0
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Completeness weights sum to {total_weight}, should be 1.0")
        
        self.completeness_indicators.update(new_weights)
        logger.info(f"Updated completeness weights: {new_weights}")
    
    def add_structural_element(self, element: str) -> None:
        """Add a new structural element to check for."""
        
        if element not in self.structural_elements:
            self.structural_elements.append(element)
            logger.info(f"Added structural element: {element}")
    
    def add_reference_pattern(self, pattern: str) -> None:
        """Add a new reference pattern to check for."""
        
        if pattern not in self.reference_patterns:
            self.reference_patterns.append(pattern)
            logger.info(f"Added reference pattern: {pattern}")