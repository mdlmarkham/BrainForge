"""AI-powered content summarization service using PydanticAI."""

import logging
from typing import Optional, Dict, Any

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from ...models.content_source import ContentSource

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """AI service for generating concise summaries of content sources."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the summarizer with a specific AI model."""
        
        try:
            self.model = OpenAIModel(model_name)
            self.agent = Agent(
                model=self.model,
                system_prompt=self._get_system_prompt(),
                retries=2
            )
            logger.info(f"ContentSummarizer initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ContentSummarizer: {e}")
            # Fallback to a basic implementation
            self.agent = None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for content summarization."""
        
        return """
        You are an expert content summarizer. Your task is to create concise, informative summaries 
        of research content while maintaining accuracy and objectivity.
        
        Guidelines:
        - Focus on key findings, methodologies, and conclusions
        - Maintain academic tone and precision
        - Keep summaries between 100-200 words
        - Highlight novel contributions and significant results
        - Avoid subjective language and personal opinions
        - Preserve technical accuracy while making content accessible
        
        Structure your summaries with:
        1. Main topic and research question
        2. Methodology approach
        3. Key findings/results
        4. Significance/contributions
        
        Always ensure the summary is factually accurate and represents the original content faithfully.
        """
    
    async def summarize_content(self, content_source: ContentSource) -> Optional[str]:
        """Generate an AI-powered summary of the content source."""
        
        try:
            # If AI agent is not available, use fallback method
            if not self.agent:
                return self._fallback_summarize(content_source)
            
            # Prepare content for summarization
            content_text = self._prepare_content_for_summarization(content_source)
            
            if not content_text:
                logger.warning(f"No content available for summarization: {content_source.url}")
                return None
            
            # Generate summary using AI
            result = await self.agent.run(
                f"Please summarize the following content:\n\n{content_text}"
            )
            
            summary = str(result.data).strip()
            
            # Validate summary quality
            if self._validate_summary(summary, content_text):
                logger.info(f"Generated summary for {content_source.url} (length: {len(summary)} chars)")
                return summary
            else:
                logger.warning(f"Summary validation failed for {content_source.url}, using fallback")
                return self._fallback_summarize(content_source)
                
        except Exception as e:
            logger.error(f"AI summarization failed for {content_source.url}: {e}")
            return self._fallback_summarize(content_source)
    
    def _prepare_content_for_summarization(self, content_source: ContentSource) -> str:
        """Prepare content text for summarization by combining relevant information."""
        
        content_parts = []
        
        # Add title if available
        if content_source.title:
            content_parts.append(f"Title: {content_source.title}")
        
        # Add description if available
        if content_source.description:
            content_parts.append(f"Description: {content_source.description}")
        
        # Add content if available (truncate if too long)
        if hasattr(content_source, 'content') and content_source.content:
            content = content_source.content
            # Truncate very long content to avoid token limits
            if len(content) > 4000:
                content = content[:4000] + "... [content truncated]"
            content_parts.append(f"Content: {content}")
        
        # Add source type and metadata context
        metadata_info = []
        if content_source.source_type:
            metadata_info.append(f"Source Type: {content_source.source_type}")
        
        if hasattr(content_source, 'metadata') and content_source.metadata:
            metadata_str = str(content_source.metadata)
            if len(metadata_str) < 500:  # Only include if not too long
                metadata_info.append(f"Metadata: {metadata_str}")
        
        if metadata_info:
            content_parts.extend(metadata_info)
        
        return "\n\n".join(content_parts)
    
    def _validate_summary(self, summary: str, original_content: str) -> bool:
        """Validate that the summary meets quality standards."""
        
        if not summary or len(summary.strip()) == 0:
            return False
        
        # Check summary length (should be reasonable)
        if len(summary) < 50:
            logger.warning("Summary too short")
            return False
        
        if len(summary) > 1000:
            logger.warning("Summary too long")
            return False
        
        # Check for common AI failure patterns
        failure_indicators = [
            "I cannot summarize", "I don't have enough information",
            "As an AI", "I'm sorry", "Unable to", "Cannot generate"
        ]
        
        for indicator in failure_indicators:
            if indicator.lower() in summary.lower():
                logger.warning(f"AI failure indicator found: {indicator}")
                return False
        
        # Check that summary contains some key elements from original
        original_words = set(original_content.lower().split()[:50])  # First 50 words
        summary_words = set(summary.lower().split())
        
        # Ensure some overlap (at least 3 significant words)
        overlap = len(original_words.intersection(summary_words))
        if overlap < 3:
            logger.warning("Summary has insufficient overlap with original content")
            return False
        
        return True
    
    def _fallback_summarize(self, content_source: ContentSource) -> str:
        """Fallback summarization method when AI is unavailable."""
        
        logger.info(f"Using fallback summarization for {content_source.url}")
        
        # Basic fallback: use description or create simple summary
        if content_source.description and len(content_source.description) > 50:
            # Use description if it's substantial
            return content_source.description
        
        elif content_source.title:
            # Create a basic summary from title
            return f"This content discusses: {content_source.title}. " \
                   f"For detailed information, please refer to the original source."
        
        else:
            # Minimal fallback
            return "Content summary unavailable. Please review the original source for details."
    
    async def summarize_multiple_contents(self, content_sources: list) -> Dict[str, Any]:
        """Generate summaries for multiple content sources with batch processing."""
        
        summaries = {}
        failed_sources = []
        
        for content_source in content_sources:
            try:
                summary = await self.summarize_content(content_source)
                if summary:
                    summaries[str(content_source.id)] = {
                        "summary": summary,
                        "source_url": content_source.url,
                        "source_title": content_source.title
                    }
                else:
                    failed_sources.append(str(content_source.id))
                    
            except Exception as e:
                logger.error(f"Failed to summarize content source {content_source.id}: {e}")
                failed_sources.append(str(content_source.id))
        
        return {
            "summaries": summaries,
            "failed_sources": failed_sources,
            "total_processed": len(content_sources),
            "successful": len(summaries),
            "failed": len(failed_sources)
        }
    
    async def generate_comparative_summary(self, content_sources: list, research_topic: str) -> Optional[str]:
        """Generate a comparative summary analyzing multiple related content sources."""
        
        try:
            if not self.agent:
                return self._fallback_comparative_summary(content_sources, research_topic)
            
            # Prepare content for comparative analysis
            comparative_prompt = self._prepare_comparative_prompt(content_sources, research_topic)
            
            result = await self.agent.run(
                f"Please analyze and compare the following sources on the topic '{research_topic}':\n\n{comparative_prompt}"
            )
            
            comparative_summary = str(result.data).strip()
            
            if self._validate_comparative_summary(comparative_summary, content_sources):
                logger.info(f"Generated comparative summary for {len(content_sources)} sources")
                return comparative_summary
            else:
                return self._fallback_comparative_summary(content_sources, research_topic)
                
        except Exception as e:
            logger.error(f"Comparative summarization failed: {e}")
            return self._fallback_comparative_summary(content_sources, research_topic)
    
    def _prepare_comparative_prompt(self, content_sources: list, research_topic: str) -> str:
        """Prepare prompt for comparative analysis."""
        
        prompt_parts = [f"Research Topic: {research_topic}\n\nSources to compare:"]
        
        for i, content_source in enumerate(content_sources, 1):
            source_info = f"\n--- Source {i} ---\n"
            source_info += f"URL: {content_source.url}\n"
            source_info += f"Title: {content_source.title}\n"
            
            if content_source.description:
                source_info += f"Description: {content_source.description}\n"
            
            prompt_parts.append(source_info)
        
        prompt_parts.append(
            "\nPlease provide a comparative analysis that:\n"
            "1. Identifies common themes across sources\n"
            "2. Highlights contrasting viewpoints or findings\n"
            "3. Notes gaps or areas needing further research\n"
            "4. Summarizes the overall state of knowledge on this topic"
        )
        
        return "\n".join(prompt_parts)
    
    def _validate_comparative_summary(self, summary: str, content_sources: list) -> bool:
        """Validate comparative summary quality."""
        
        if not summary or len(summary.strip()) < 100:
            return False
        
        # Check that summary references multiple sources
        source_references = 0
        for content_source in content_sources:
            if content_source.title and content_source.title.lower() in summary.lower():
                source_references += 1
        
        if source_references < min(2, len(content_sources)):
            logger.warning("Comparative summary doesn't reference enough sources")
            return False
        
        return True
    
    def _fallback_comparative_summary(self, content_sources: list, research_topic: str) -> str:
        """Fallback for comparative summarization."""
        
        source_count = len(content_sources)
        return f"Comparative analysis of {source_count} sources on '{research_topic}'. " \
               f"Key sources include: {', '.join([cs.title for cs in content_sources if cs.title][:3])}. " \
               f"Please review individual sources for detailed analysis."