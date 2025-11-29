"""Credibility scoring service for evaluating content trustworthiness."""

import logging
import re
from typing import Dict, Any, List
from urllib.parse import urlparse

from ...models.content_source import ContentSource

logger = logging.getLogger(__name__)


class CredibilityScorer:
    """Scores content credibility based on source reputation, content quality, and trust indicators."""
    
    def __init__(self):
        # Domain reputation database (would typically be external)
        self.trusted_domains = {
            "edu": 0.9,  # Educational institutions
            "gov": 0.9,  # Government sources
            "org": 0.7,  # Non-profits
            "com": 0.5,  # Commercial sites
            "net": 0.5,  # Network sites
        }
        
        # Known reputable domains
        self.reputable_domains = {
            "wikipedia.org": 0.8,
            "arxiv.org": 0.9,
            "nih.gov": 0.9,
            "nasa.gov": 0.9,
            "nature.com": 0.8,
            "science.org": 0.8,
            "ieee.org": 0.8,
            "acm.org": 0.8,
        }
        
        # Known low-reputation domains
        self.low_reputation_domains = {
            "blogspot.com": 0.3,
            "wordpress.com": 0.4,
            "medium.com": 0.4,
            "tumblr.com": 0.3,
        }
    
    async def score_content(self, content_source: ContentSource) -> float:
        """Score content credibility on a scale of 0.0 to 1.0."""
        
        try:
            scores = []
            weights = []
            
            # 1. Domain reputation scoring
            domain_score = self._score_domain_reputation(content_source.url)
            scores.append(domain_score)
            weights.append(0.4)  # 40% weight
            
            # 2. Content quality indicators
            content_score = self._score_content_quality(content_source)
            scores.append(content_score)
            weights.append(0.3)  # 30% weight
            
            # 3. Author/Publisher credibility
            author_score = self._score_author_credibility(content_source)
            scores.append(author_score)
            weights.append(0.2)  # 20% weight
            
            # 4. External validation indicators
            validation_score = self._score_external_validation(content_source)
            scores.append(validation_score)
            weights.append(0.1)  # 10% weight
            
            # Calculate weighted average
            weighted_score = sum(score * weight for score, weight in zip(scores, weights))
            weighted_score = max(0.0, min(1.0, weighted_score))  # Clamp to 0-1 range
            
            logger.debug(f"Credibility scoring for {content_source.url}: "
                        f"domain={domain_score:.2f}, content={content_score:.2f}, "
                        f"author={author_score:.2f}, validation={validation_score:.2f}, "
                        f"final={weighted_score:.2f}")
            
            return round(weighted_score, 2)
            
        except Exception as e:
            logger.error(f"Error scoring credibility for {content_source.url}: {e}")
            return 0.5  # Default neutral score on error
    
    def _score_domain_reputation(self, url: str) -> float:
        """Score domain reputation based on TLD and known domain reputation."""
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check for exact domain matches first
            for known_domain, score in self.reputable_domains.items():
                if known_domain in domain:
                    return score
            
            # Check for low reputation domains
            for low_domain, score in self.low_reputation_domains.items():
                if low_domain in domain:
                    return score
            
            # Check TLD-based scoring
            tld = domain.split('.')[-1] if '.' in domain else ''
            if tld in self.trusted_domains:
                return self.trusted_domains[tld]
            
            # Default score for unknown domains
            return 0.5
            
        except Exception as e:
            logger.warning(f"Error parsing domain from {url}: {e}")
            return 0.5
    
    def _score_content_quality(self, content_source: ContentSource) -> float:
        """Score content quality based on structural and linguistic indicators."""
        
        score = 0.5  # Base score
        
        # Analyze title quality
        title_score = self._analyze_title_quality(content_source.title)
        score += title_score * 0.2
        
        # Analyze description quality
        description_score = self._analyze_description_quality(content_source.description)
        score += description_score * 0.2
        
        # Analyze content structure indicators (if available)
        if hasattr(content_source, 'content') and content_source.content:
            structure_score = self._analyze_content_structure(content_source.content)
            score += structure_score * 0.3
        
        # Source type scoring
        source_type_score = self._score_source_type(content_source.source_type)
        score += source_type_score * 0.3
        
        return max(0.0, min(1.0, score))
    
    def _analyze_title_quality(self, title: str) -> float:
        """Analyze title quality for credibility indicators."""
        
        if not title:
            return 0.3
        
        score = 0.5
        
        # Positive indicators
        positive_patterns = [
            r'\b(study|research|analysis|findings|evidence|data)\b',
            r'\b(peer.?reviewed|academic|scientific)\b',
            r'\b(journal|conference|proceedings)\b',
        ]
        
        for pattern in positive_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                score += 0.1
        
        # Negative indicators (clickbait, sensationalism)
        negative_patterns = [
            r'\b(shocking|amazing|incredible|unbelievable)\b',
            r'\!+$',  # Multiple exclamation marks
            r'\?+$',  # Multiple question marks
            r'\b(you won\'t believe|this will blow your mind)\b',
        ]
        
        for pattern in negative_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                score -= 0.2
        
        # Length-based scoring (moderate length is best)
        title_length = len(title.split())
        if 5 <= title_length <= 15:
            score += 0.1
        elif title_length > 20:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _analyze_description_quality(self, description: str) -> float:
        """Analyze description quality for credibility indicators."""
        
        if not description:
            return 0.3
        
        score = 0.5
        
        # Positive indicators
        positive_indicators = [
            "study found", "research shows", "according to", "evidence suggests",
            "data indicates", "analysis reveals", "findings demonstrate"
        ]
        
        for indicator in positive_indicators:
            if indicator.lower() in description.lower():
                score += 0.05
        
        # Length-based scoring
        desc_length = len(description.split())
        if 20 <= desc_length <= 100:
            score += 0.1
        elif desc_length < 10:
            score -= 0.2
        
        # Professional language indicators
        professional_terms = ["methodology", "hypothesis", "results", "conclusion", "abstract"]
        for term in professional_terms:
            if term.lower() in description.lower():
                score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _analyze_content_structure(self, content: str) -> float:
        """Analyze content structure for credibility indicators."""
        
        if not content:
            return 0.3
        
        score = 0.5
        
        # Check for structured elements
        structure_indicators = [
            "introduction", "method", "results", "discussion", "conclusion",
            "abstract", "references", "bibliography"
        ]
        
        found_indicators = 0
        for indicator in structure_indicators:
            if indicator.lower() in content.lower():
                found_indicators += 1
        
        if found_indicators >= 3:
            score += 0.3
        elif found_indicators >= 1:
            score += 0.1
        
        # Check for citation patterns
        citation_patterns = [
            r'\(\d{4}\)',  # (2024)
            r'\[?\d+\]?',  # [1] or 1
            r'et al\.',    # et al.
            r'pp\. \d+',   # pp. 123
        ]
        
        citation_count = 0
        for pattern in citation_patterns:
            citation_count += len(re.findall(pattern, content))
        
        if citation_count >= 5:
            score += 0.2
        elif citation_count >= 2:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _score_source_type(self, source_type: str) -> float:
        """Score credibility based on source type."""
        
        source_type_scores = {
            "academic_paper": 0.9,
            "journal_article": 0.8,
            "conference_paper": 0.8,
            "technical_report": 0.7,
            "government_report": 0.8,
            "news_article": 0.6,
            "blog_post": 0.4,
            "forum_post": 0.3,
            "social_media": 0.2,
            "unknown": 0.5,
        }
        
        return source_type_scores.get(source_type, 0.5)
    
    def _score_author_credibility(self, content_source: ContentSource) -> float:
        """Score author/publisher credibility."""
        
        # This would typically integrate with external author reputation databases
        # For now, use basic heuristics
        
        score = 0.5
        
        # Check for institutional affiliation in metadata
        if hasattr(content_source, 'metadata') and content_source.metadata:
            metadata = content_source.metadata
            
            # Institutional indicators
            institutional_indicators = [
                "university", "college", "institute", "research center",
                "laboratory", "department", "faculty"
            ]
            
            metadata_str = str(metadata).lower()
            for indicator in institutional_indicators:
                if indicator in metadata_str:
                    score += 0.2
                    break
        
        # Author name presence (basic indicator)
        if hasattr(content_source, 'author') and content_source.author:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _score_external_validation(self, content_source: ContentSource) -> float:
        """Score external validation indicators."""
        
        score = 0.5
        
        # This would typically check:
        # - Citation count from external databases
        # - Social media shares (with credibility weighting)
        # - Peer review status
        # - Fact-checking results
        
        # For now, use basic heuristics based on available metadata
        if hasattr(content_source, 'metadata') and content_source.metadata:
            metadata = content_source.metadata
            
            # Check for peer review indicators
            if isinstance(metadata, dict):
                if metadata.get('peer_reviewed'):
                    score += 0.3
                if metadata.get('citation_count', 0) > 10:
                    score += 0.2
        
        return max(0.0, min(1.0, score))