"""Relevance scoring service for evaluating content alignment with research topics."""

import logging
import re
from typing import Dict, Any, List
from difflib import SequenceMatcher

from ...models.content_source import ContentSource

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Scores content relevance based on topic alignment, keyword matching, and semantic similarity."""
    
    def __init__(self):
        # Topic-specific keyword weights (would typically be configurable)
        self.topic_keywords = {
            "artificial intelligence": ["ai", "machine learning", "neural network", "deep learning"],
            "machine learning": ["ml", "algorithm", "training", "model", "prediction"],
            "data science": ["data analysis", "statistics", "visualization", "big data"],
            "software engineering": ["programming", "development", "code", "architecture", "testing"],
            "cybersecurity": ["security", "encryption", "vulnerability", "threat", "attack"],
            "cloud computing": ["cloud", "aws", "azure", "gcp", "infrastructure"],
        }
        
        # Stop words to ignore in relevance scoring
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being"
        }
    
    async def score_content(self, content_source: ContentSource, research_topic: str = None) -> float:
        """Score content relevance on a scale of 0.0 to 1.0."""
        
        try:
            # If no specific research topic provided, use content source context
            if not research_topic and hasattr(content_source, 'research_topic'):
                research_topic = content_source.research_topic
            
            if not research_topic:
                logger.warning("No research topic provided for relevance scoring")
                return 0.5  # Neutral score
            
            scores = []
            weights = []
            
            # 1. Keyword matching scoring
            keyword_score = self._score_keyword_matching(content_source, research_topic)
            scores.append(keyword_score)
            weights.append(0.4)  # 40% weight
            
            # 2. Semantic similarity scoring
            semantic_score = self._score_semantic_similarity(content_source, research_topic)
            scores.append(semantic_score)
            weights.append(0.3)  # 30% weight
            
            # 3. Topic alignment scoring
            topic_score = self._score_topic_alignment(content_source, research_topic)
            scores.append(topic_score)
            weights.append(0.2)  # 20% weight
            
            # 4. Content depth scoring
            depth_score = self._score_content_depth(content_source, research_topic)
            scores.append(depth_score)
            weights.append(0.1)  # 10% weight
            
            # Calculate weighted average
            weighted_score = sum(score * weight for score, weight in zip(scores, weights))
            weighted_score = max(0.0, min(1.0, weighted_score))  # Clamp to 0-1 range
            
            logger.debug(f"Relevance scoring for {content_source.url} on topic '{research_topic}': "
                        f"keyword={keyword_score:.2f}, semantic={semantic_score:.2f}, "
                        f"topic={topic_score:.2f}, depth={depth_score:.2f}, "
                        f"final={weighted_score:.2f}")
            
            return round(weighted_score, 2)
            
        except Exception as e:
            logger.error(f"Error scoring relevance for {content_source.url}: {e}")
            return 0.5  # Default neutral score on error
    
    def _score_keyword_matching(self, content_source: ContentSource, research_topic: str) -> float:
        """Score based on keyword matching between research topic and content."""
        
        # Extract keywords from research topic
        topic_keywords = self._extract_keywords(research_topic)
        
        # Combine content text for analysis
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        # Calculate keyword matches
        matches = 0
        total_keywords = len(topic_keywords)
        
        if total_keywords == 0:
            return 0.5
        
        for keyword in topic_keywords:
            # Use case-insensitive matching with word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, content_text, re.IGNORECASE):
                matches += 1
        
        # Calculate match ratio
        match_ratio = matches / total_keywords
        
        # Apply non-linear scaling (exponential decay for better discrimination)
        if match_ratio == 0:
            score = 0.1
        elif match_ratio < 0.3:
            score = 0.3 + (match_ratio * 0.4)
        elif match_ratio < 0.7:
            score = 0.5 + ((match_ratio - 0.3) * 0.4)
        else:
            score = 0.7 + ((match_ratio - 0.7) * 0.3)
        
        return max(0.0, min(1.0, score))
    
    def _score_semantic_similarity(self, content_source: ContentSource, research_topic: str) -> float:
        """Score based on semantic similarity using text similarity algorithms."""
        
        # This would typically use more sophisticated NLP techniques
        # For now, use basic string similarity
        
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        # Use SequenceMatcher for basic similarity
        similarity = SequenceMatcher(None, research_topic.lower(), content_text.lower()).ratio()
        
        # Apply scaling to make scores more discriminative
        if similarity < 0.1:
            score = 0.1
        elif similarity < 0.3:
            score = 0.3 + ((similarity - 0.1) * 0.7)
        else:
            score = 0.7 + ((similarity - 0.3) * 0.3)
        
        return max(0.0, min(1.0, score))
    
    def _score_topic_alignment(self, content_source: ContentSource, research_topic: str) -> float:
        """Score based on broader topic alignment beyond exact keywords."""
        
        # Normalize research topic for comparison
        normalized_topic = research_topic.lower().strip()
        
        # Get content topic indicators
        content_topic_indicators = self._extract_topic_indicators(content_source)
        
        if not content_topic_indicators:
            return 0.3
        
        # Calculate topic overlap
        overlap_score = 0.0
        
        for indicator in content_topic_indicators:
            # Check if research topic contains indicator or vice versa
            if indicator in normalized_topic or normalized_topic in indicator:
                overlap_score += 0.2
            else:
                # Check for partial matches
                if self._calculate_partial_match(normalized_topic, indicator) > 0.6:
                    overlap_score += 0.1
        
        return max(0.0, min(1.0, overlap_score))
    
    def _score_content_depth(self, content_source: ContentSource, research_topic: str) -> float:
        """Score based on content depth and comprehensiveness related to the topic."""
        
        content_text = self._get_content_text(content_source)
        
        if not content_text:
            return 0.3
        
        score = 0.5
        
        # Length-based scoring (longer content tends to be more comprehensive)
        word_count = len(content_text.split())
        if word_count > 1000:
            score += 0.2
        elif word_count > 500:
            score += 0.1
        elif word_count < 100:
            score -= 0.2
        
        # Check for depth indicators
        depth_indicators = [
            "methodology", "analysis", "results", "discussion", "conclusion",
            "experiment", "study", "research", "findings", "data"
        ]
        
        found_indicators = 0
        for indicator in depth_indicators:
            if indicator.lower() in content_text.lower():
                found_indicators += 1
        
        if found_indicators >= 3:
            score += 0.3
        elif found_indicators >= 1:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        
        if not text:
            return []
        
        # Basic keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out stop words and duplicates
        keywords = []
        for word in words:
            if (word not in self.stop_words and 
                word not in keywords and 
                len(word) > 2):
                keywords.append(word)
        
        return keywords
    
    def _get_content_text(self, content_source: ContentSource) -> str:
        """Extract combined text from content source for analysis."""
        
        text_parts = []
        
        # Add title if available
        if content_source.title:
            text_parts.append(content_source.title)
        
        # Add description if available
        if content_source.description:
            text_parts.append(content_source.description)
        
        # Add content if available (from metadata or separate field)
        if hasattr(content_source, 'content') and content_source.content:
            text_parts.append(content_source.content)
        
        # Add metadata as string if available
        if hasattr(content_source, 'metadata') and content_source.metadata:
            text_parts.append(str(content_source.metadata))
        
        return " ".join(text_parts)
    
    def _extract_topic_indicators(self, content_source: ContentSource) -> List[str]:
        """Extract topic indicators from content source."""
        
        indicators = []
        
        # Use source type as indicator
        if content_source.source_type:
            indicators.append(content_source.source_type)
        
        # Extract from title and description
        content_text = self._get_content_text(content_source)
        if content_text:
            # Extract potential topic words (nouns and important terms)
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content_text.lower())
            
            # Filter for potential topic words (excluding common words)
            topic_words = [word for word in words 
                          if word not in self.stop_words 
                          and len(word) > 3]
            
            # Take top 5 most frequent words as indicators
            from collections import Counter
            if topic_words:
                word_freq = Counter(topic_words)
                top_words = [word for word, _ in word_freq.most_common(5)]
                indicators.extend(top_words)
        
        return indicators
    
    def _calculate_partial_match(self, text1: str, text2: str) -> float:
        """Calculate partial match similarity between two texts."""
        
        if not text1 or not text2:
            return 0.0
        
        # Use word-level similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    async def get_relevance_breakdown(self, content_source: ContentSource, research_topic: str) -> Dict[str, Any]:
        """Get detailed relevance scoring breakdown."""
        
        keyword_score = self._score_keyword_matching(content_source, research_topic)
        semantic_score = self._score_semantic_similarity(content_source, research_topic)
        topic_score = self._score_topic_alignment(content_source, research_topic)
        depth_score = self._score_content_depth(content_source, research_topic)
        
        overall_score = await self.score_content(content_source, research_topic)
        
        return {
            "overall_score": overall_score,
            "breakdown": {
                "keyword_matching": {
                    "score": keyword_score,
                    "weight": 0.4,
                    "contribution": keyword_score * 0.4
                },
                "semantic_similarity": {
                    "score": semantic_score,
                    "weight": 0.3,
                    "contribution": semantic_score * 0.3
                },
                "topic_alignment": {
                    "score": topic_score,
                    "weight": 0.2,
                    "contribution": topic_score * 0.2
                },
                "content_depth": {
                    "score": depth_score,
                    "weight": 0.1,
                    "contribution": depth_score * 0.1
                }
            },
            "research_topic": research_topic,
            "content_source_id": str(content_source.id) if hasattr(content_source, 'id') else None
        }