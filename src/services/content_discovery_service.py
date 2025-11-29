"""Content Discovery Service for finding external content from various sources."""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.content_source import ContentSource, ContentSourceCreate, ContentSourceType
from ..models.research_run import ResearchRun
from .research_run_service import ResearchRunService
from .external.google_search import GoogleSearchClient
from .external.semantic_scholar import SemanticScholarClient
from .external.news_api import NewsAPIClient

logger = logging.getLogger(__name__)


class ContentDiscoveryService:
    """Service for discovering content from external sources based on research topics."""
    
    def __init__(self):
        self.research_run_service = ResearchRunService()
        self.google_search = GoogleSearchClient()
        self.semantic_scholar = SemanticScholarClient()
        self.news_api = NewsAPIClient()
    
    async def discover_content(
        self,
        session: AsyncSession,
        research_run_id: UUID,
        research_topic: str,
        max_sources: int = 50
    ) -> List[ContentSource]:
        """Discover content from multiple external sources for a research topic."""
        
        logger.info(f"Starting content discovery for research run {research_run_id}: {research_topic}")
        
        # Update research run status to running
        await self.research_run_service.start_research_run(session, research_run_id)
        
        try:
            # Discover content from different sources in parallel
            discovery_tasks = [
                self._discover_web_content(session, research_run_id, research_topic, max_sources // 3),
                self._discover_academic_content(session, research_run_id, research_topic, max_sources // 3),
                self._discover_news_content(session, research_run_id, research_topic, max_sources // 3)
            ]
            
            results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
            
            # Flatten results and filter out exceptions
            all_sources = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Content discovery error: {result}")
                elif result:
                    all_sources.extend(result)
            
            # Deduplicate sources by content hash
            unique_sources = self._deduplicate_sources(all_sources)
            
            logger.info(f"Discovered {len(unique_sources)} unique sources for research run {research_run_id}")
            
            # Update research run metrics
            await self.research_run_service.update_research_metrics(
                session, research_run_id, sources_discovered=len(unique_sources)
            )
            
            return unique_sources
            
        except Exception as e:
            logger.error(f"Content discovery failed for research run {research_run_id}: {e}")
            await self.research_run_service.fail_research_run(session, research_run_id, str(e))
            raise
    
    async def _discover_web_content(
        self,
        session: AsyncSession,
        research_run_id: UUID,
        research_topic: str,
        max_results: int
    ) -> List[ContentSource]:
        """Discover web content using Google Custom Search."""
        
        try:
            search_results = await self.google_search.search(research_topic, max_results)
            sources = []
            
            for result in search_results:
                content_hash = self._generate_content_hash(result.get('url', ''))
                
                source = ContentSourceCreate(
                    research_run_id=research_run_id,
                    source_type=ContentSourceType.WEB_ARTICLE,
                    source_url=result.get('url', ''),
                    source_title=result.get('title', ''),
                    source_metadata={
                        'snippet': result.get('snippet', ''),
                        'display_url': result.get('displayLink', ''),
                        'search_engine': 'google'
                    },
                    retrieval_method='google_custom_search',
                    retrieval_timestamp=datetime.now(),
                    content_hash=content_hash
                )
                
                sources.append(source)
            
            logger.info(f"Discovered {len(sources)} web sources for topic: {research_topic}")
            return sources
            
        except Exception as e:
            logger.error(f"Web content discovery failed: {e}")
            return []
    
    async def _discover_academic_content(
        self,
        session: AsyncSession,
        research_run_id: UUID,
        research_topic: str,
        max_results: int
    ) -> List[ContentSource]:
        """Discover academic content using Semantic Scholar."""
        
        try:
            papers = await self.semantic_scholar.search_papers(research_topic, max_results)
            sources = []
            
            for paper in papers:
                content_hash = self._generate_content_hash(paper.get('paperId', ''))
                
                source = ContentSourceCreate(
                    research_run_id=research_run_id,
                    source_type=ContentSourceType.ACADEMIC_PAPER,
                    source_url=paper.get('url', ''),
                    source_title=paper.get('title', ''),
                    source_metadata={
                        'authors': paper.get('authors', []),
                        'abstract': paper.get('abstract', ''),
                        'venue': paper.get('venue', ''),
                        'year': paper.get('year', ''),
                        'citation_count': paper.get('citationCount', 0)
                    },
                    retrieval_method='semantic_scholar',
                    retrieval_timestamp=datetime.now(),
                    content_hash=content_hash
                )
                
                sources.append(source)
            
            logger.info(f"Discovered {len(sources)} academic sources for topic: {research_topic}")
            return sources
            
        except Exception as e:
            logger.error(f"Academic content discovery failed: {e}")
            return []
    
    async def _discover_news_content(
        self,
        session: AsyncSession,
        research_run_id: UUID,
        research_topic: str,
        max_results: int
    ) -> List[ContentSource]:
        """Discover news content using NewsAPI."""
        
        try:
            articles = await self.news_api.search_articles(research_topic, max_results)
            sources = []
            
            for article in articles:
                content_hash = self._generate_content_hash(article.get('url', ''))
                
                source = ContentSourceCreate(
                    research_run_id=research_run_id,
                    source_type=ContentSourceType.NEWS_REPORT,
                    source_url=article.get('url', ''),
                    source_title=article.get('title', ''),
                    source_metadata={
                        'description': article.get('description', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'published_at': article.get('publishedAt', ''),
                        'author': article.get('author', '')
                    },
                    retrieval_method='news_api',
                    retrieval_timestamp=datetime.now(),
                    content_hash=content_hash
                )
                
                sources.append(source)
            
            logger.info(f"Discovered {len(sources)} news sources for topic: {research_topic}")
            return sources
            
        except Exception as e:
            logger.error(f"News content discovery failed: {e}")
            return []
    
    def _generate_content_hash(self, content_identifier: str) -> str:
        """Generate a hash for content deduplication."""
        return hashlib.sha256(content_identifier.encode()).hexdigest()
    
    def _deduplicate_sources(self, sources: List[ContentSource]) -> List[ContentSource]:
        """Deduplicate sources based on content hash."""
        seen_hashes = set()
        unique_sources = []
        
        for source in sources:
            if source.content_hash not in seen_hashes:
                seen_hashes.add(source.content_hash)
                unique_sources.append(source)
        
        return unique_sources
    
    async def get_content_sources_for_research_run(
        self,
        session: AsyncSession,
        research_run_id: UUID
    ) -> List[ContentSource]:
        """Get all content sources for a specific research run."""
        
        # This would typically query the database for content sources
        # For now, return empty list as we haven't implemented the database query yet
        return []