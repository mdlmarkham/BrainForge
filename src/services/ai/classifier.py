"""AI-powered content classification service using PydanticAI."""

import logging
from typing import List, Dict, Any, Optional

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel

from ...models.content_source import ContentSource

logger = logging.getLogger(__name__)


class ContentClassification(BaseModel):
    """Model for content classification results."""
    
    primary_topic: str
    secondary_topics: List[str]
    content_type: str
    academic_level: str
    technical_depth: str
    confidence_score: float


class ContentClassifier:
    """AI service for classifying content sources by topic, type, and characteristics."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the classifier with a specific AI model."""
        
        try:
            self.model = OpenAIModel(model_name)
            self.agent = Agent(
                model=self.model,
                system_prompt=self._get_system_prompt(),
                retries=2
            )
            logger.info(f"ContentClassifier initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ContentClassifier: {e}")
            # Fallback to a basic implementation
            self.agent = None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for content classification."""
        
        return """
        You are an expert content classifier. Your task is to analyze research content and classify it 
        according to topic, type, academic level, and technical depth.
        
        Classification Categories:
        
        Primary Topic: Identify the main subject area (e.g., Artificial Intelligence, Biology, Economics)
        Secondary Topics: List related sub-topics or adjacent areas
        
        Content Type: Choose from:
        - Research Paper
        - Review Article
        - Technical Report
        - News Article
        - Blog Post
        - Tutorial/Guide
        - Opinion Piece
        - Case Study
        - White Paper
        - Other
        
        Academic Level: Choose from:
        - Introductory (basic concepts, overview)
        - Intermediate (assumes some background knowledge)
        - Advanced (specialized, technical depth)
        - Expert (cutting-edge research, highly technical)
        
        Technical Depth: Choose from:
        - Non-technical (accessible to general audience)
        - Lightly Technical (some technical concepts explained)
        - Moderately Technical (assumes technical background)
        - Highly Technical (specialized terminology, complex concepts)
        
        Provide a confidence score from 0.0 to 1.0 indicating how confident you are in the classification.
        
        Be objective and base your classification solely on the content provided.
        """
    
    async def classify_content(self, content_source: ContentSource) -> Optional[ContentClassification]:
        """Classify a content source using AI."""
        
        try:
            # If AI agent is not available, use fallback method
            if not self.agent:
                return self._fallback_classify(content_source)
            
            # Prepare content for classification
            content_text = self._prepare_content_for_classification(content_source)
            
            if not content_text:
                logger.warning(f"No content available for classification: {content_source.url}")
                return None
            
            # Generate classification using AI
            result = await self.agent.run(
                f"Please classify the following content:\n\n{content_text}"
            )
            
            # Parse the AI response into structured classification
            classification = self._parse_classification_response(str(result.data))
            
            if classification and self._validate_classification(classification):
                logger.info(f"Classified {content_source.url} as: {classification.primary_topic}")
                return classification
            else:
                logger.warning(f"Classification validation failed for {content_source.url}, using fallback")
                return self._fallback_classify(content_source)
                
        except Exception as e:
            logger.error(f"AI classification failed for {content_source.url}: {e}")
            return self._fallback_classify(content_source)
    
    def _prepare_content_for_classification(self, content_source: ContentSource) -> str:
        """Prepare content text for classification by combining relevant information."""
        
        content_parts = []
        
        # Add title if available (often most informative for classification)
        if content_source.title:
            content_parts.append(f"Title: {content_source.title}")
        
        # Add description if available
        if content_source.description:
            content_parts.append(f"Description: {content_source.description}")
        
        # Add content if available (use beginning for efficiency)
        if hasattr(content_source, 'content') and content_source.content:
            content = content_source.content
            # Use first 1000 characters for classification (usually sufficient)
            if len(content) > 1000:
                content = content[:1000] + "..."
            content_parts.append(f"Content Excerpt: {content}")
        
        # Add source type for context
        if content_source.source_type:
            content_parts.append(f"Source Type: {content_source.source_type}")
        
        return "\n\n".join(content_parts)
    
    def _parse_classification_response(self, response: str) -> Optional[ContentClassification]:
        """Parse AI response into structured classification."""
        
        try:
            # This would typically use more sophisticated parsing
            # For now, use basic keyword-based parsing
            
            # Extract primary topic (look for topic indicators)
            primary_topic = self._extract_primary_topic(response)
            
            # Extract secondary topics
            secondary_topics = self._extract_secondary_topics(response)
            
            # Extract content type
            content_type = self._extract_content_type(response)
            
            # Extract academic level
            academic_level = self._extract_academic_level(response)
            
            # Extract technical depth
            technical_depth = self._extract_technical_depth(response)
            
            # Extract confidence score
            confidence_score = self._extract_confidence_score(response)
            
            return ContentClassification(
                primary_topic=primary_topic,
                secondary_topics=secondary_topics,
                content_type=content_type,
                academic_level=academic_level,
                technical_depth=technical_depth,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            return None
    
    def _extract_primary_topic(self, response: str) -> str:
        """Extract primary topic from AI response."""
        
        # Common topic keywords to look for
        topic_keywords = {
            "artificial intelligence": ["ai", "machine learning", "neural network"],
            "computer science": ["algorithm", "programming", "software", "computer"],
            "biology": ["biology", "genetics", "cells", "organism"],
            "physics": ["physics", "quantum", "relativity", "particle"],
            "chemistry": ["chemistry", "molecule", "reaction", "compound"],
            "economics": ["economics", "market", "finance", "economic"],
            "psychology": ["psychology", "behavior", "cognitive", "mental"],
            "medicine": ["medicine", "medical", "health", "disease"],
            "engineering": ["engineering", "design", "system", "mechanical"],
            "mathematics": ["mathematics", "math", "equation", "theorem"],
        }
        
        response_lower = response.lower()
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in response_lower:
                    return topic
        
        # Fallback: use first few words or "Unknown"
        words = response.split()[:3]
        return " ".join(words) if words else "Unknown"
    
    def _extract_secondary_topics(self, response: str) -> List[str]:
        """Extract secondary topics from AI response."""
        
        # Simple implementation - would be more sophisticated in production
        secondary_topics = []
        response_lower = response.lower()
        
        # Look for topic indicators beyond the primary topic
        topic_indicators = [
            "also discusses", "related to", "secondary topics", "additional areas",
            "including", "covering", "topics include"
        ]
        
        # This is a simplified implementation
        # In production, this would use more advanced NLP
        if "technology" in response_lower and "technology" not in secondary_topics:
            secondary_topics.append("Technology")
        
        if "research" in response_lower and "Research" not in secondary_topics:
            secondary_topics.append("Research Methods")
        
        return secondary_topics[:3]  # Limit to top 3
    
    def _extract_content_type(self, response: str) -> str:
        """Extract content type from AI response."""
        
        response_lower = response.lower()
        
        content_types = [
            "research paper", "review article", "technical report", "news article",
            "blog post", "tutorial", "guide", "opinion piece", "case study", "white paper"
        ]
        
        for content_type in content_types:
            if content_type in response_lower:
                return content_type.title()
        
        return "Other"
    
    def _extract_academic_level(self, response: str) -> str:
        """Extract academic level from AI response."""
        
        response_lower = response.lower()
        
        if "introductory" in response_lower or "basic" in response_lower:
            return "Introductory"
        elif "intermediate" in response_lower:
            return "Intermediate"
        elif "advanced" in response_lower or "specialized" in response_lower:
            return "Advanced"
        elif "expert" in response_lower or "cutting-edge" in response_lower:
            return "Expert"
        
        return "Intermediate"  # Default
    
    def _extract_technical_depth(self, response: str) -> str:
        """Extract technical depth from AI response."""
        
        response_lower = response.lower()
        
        if "non-technical" in response_lower or "general audience" in response_lower:
            return "Non-technical"
        elif "lightly technical" in response_lower or "some technical" in response_lower:
            return "Lightly Technical"
        elif "moderately technical" in response_lower or "technical background" in response_lower:
            return "Moderately Technical"
        elif "highly technical" in response_lower or "complex concepts" in response_lower:
            return "Highly Technical"
        
        return "Moderately Technical"  # Default
    
    def _extract_confidence_score(self, response: str) -> float:
        """Extract confidence score from AI response."""
        
        # Look for confidence indicators
        response_lower = response.lower()
        
        if "high confidence" in response_lower or "very confident" in response_lower:
            return 0.9
        elif "moderate confidence" in response_lower or "fairly confident" in response_lower:
            return 0.7
        elif "low confidence" in response_lower or "uncertain" in response_lower:
            return 0.4
        
        # Default confidence
        return 0.6
    
    def _validate_classification(self, classification: ContentClassification) -> bool:
        """Validate that the classification meets quality standards."""
        
        if not classification.primary_topic or classification.primary_topic == "Unknown":
            return False
        
        if classification.confidence_score < 0.1 or classification.confidence_score > 1.0:
            return False
        
        # Validate content type is from allowed list
        allowed_content_types = [
            "Research Paper", "Review Article", "Technical Report", "News Article",
            "Blog Post", "Tutorial", "Guide", "Opinion Piece", "Case Study", "White Paper", "Other"
        ]
        
        if classification.content_type not in allowed_content_types:
            return False
        
        return True
    
    def _fallback_classify(self, content_source: ContentSource) -> ContentClassification:
        """Fallback classification method when AI is unavailable."""
        
        logger.info(f"Using fallback classification for {content_source.url}")
        
        # Basic fallback classification based on source type and title
        primary_topic = "General"
        content_type = "Other"
        
        if content_source.source_type:
            if "academic" in content_source.source_type.lower():
                content_type = "Research Paper"
                primary_topic = "Academic Research"
            elif "news" in content_source.source_type.lower():
                content_type = "News Article"
                primary_topic = "Current Affairs"
            elif "blog" in content_source.source_type.lower():
                content_type = "Blog Post"
                primary_topic = "Opinion/Analysis"
        
        # Try to extract topic from title
        if content_source.title:
            title_lower = content_source.title.lower()
            if any(keyword in title_lower for keyword in ["ai", "artificial intelligence", "machine learning"]):
                primary_topic = "Artificial Intelligence"
            elif any(keyword in title_lower for keyword in ["software", "programming", "code"]):
                primary_topic = "Software Engineering"
            elif any(keyword in title_lower for keyword in ["data", "analysis", "statistics"]):
                primary_topic = "Data Science"
        
        return ContentClassification(
            primary_topic=primary_topic,
            secondary_topics=[],
            content_type=content_type,
            academic_level="Intermediate",
            technical_depth="Moderately Technical",
            confidence_score=0.5
        )
    
    async def classify_multiple_contents(self, content_sources: list) -> Dict[str, Any]:
        """Classify multiple content sources with batch processing."""
        
        classifications = {}
        failed_sources = []
        
        for content_source in content_sources:
            try:
                classification = await self.classify_content(content_source)
                if classification:
                    classifications[str(content_source.id)] = {
                        "classification": classification.model_dump(),
                        "source_url": content_source.url,
                        "source_title": content_source.title
                    }
                else:
                    failed_sources.append(str(content_source.id))
                    
            except Exception as e:
                logger.error(f"Failed to classify content source {content_source.id}: {e}")
                failed_sources.append(str(content_source.id))
        
        return {
            "classifications": classifications,
            "failed_sources": failed_sources,
            "total_processed": len(content_sources),
            "successful": len(classifications),
            "failed": len(failed_sources)
        }