"""NewsAPI client for news content discovery."""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class NewsAPIClient:
    """Client for NewsAPI."""
    
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"
        
        if not self.api_key:
            logger.warning("NewsAPI key not configured")
    
    async def search_articles(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for news articles using NewsAPI."""
        
        if not self.api_key:
            logger.error("NewsAPI not configured")
            return []
        
        try:
            # Calculate date range (last 30 days)
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            params = {
                'q': query,
                'from': from_date,
                'to': to_date,
                'sortBy': 'relevancy',
                'pageSize': min(100, max_results),  # NewsAPI max is 100 per request
                'apiKey': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/everything", params=params)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get('articles', [])
                
                logger.info(f"NewsAPI found {len(articles)} articles for query: {query}")
                return articles[:max_results]
            
        except httpx.HTTPError as e:
            logger.error(f"NewsAPI HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []
    
    async def get_top_headlines(self, category: str = "general", max_results: int = 10) -> List[Dict[str, Any]]:
        """Get top headlines from NewsAPI."""
        
        if not self.api_key:
            logger.error("NewsAPI not configured")
            return []
        
        try:
            params = {
                'category': category,
                'pageSize': min(100, max_results),
                'apiKey': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/top-headlines", params=params)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get('articles', [])
                
                logger.info(f"NewsAPI found {len(articles)} top headlines for category: {category}")
                return articles[:max_results]
            
        except httpx.HTTPError as e:
            logger.error(f"NewsAPI top headlines HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"NewsAPI top headlines error: {e}")
            return []
    
    async def get_articles_by_source(self, source: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get articles from a specific news source."""
        
        if not self.api_key:
            logger.error("NewsAPI not configured")
            return []
        
        try:
            params = {
                'sources': source,
                'pageSize': min(100, max_results),
                'apiKey': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/everything", params=params)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get('articles', [])
                
                logger.info(f"NewsAPI found {len(articles)} articles from source: {source}")
                return articles[:max_results]
            
        except httpx.HTTPError as e:
            logger.error(f"NewsAPI source articles HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"NewsAPI source articles error: {e}")
            return []
    
    async def get_sources(self, category: str = "general", language: str = "en") -> List[Dict[str, Any]]:
        """Get available news sources from NewsAPI."""
        
        if not self.api_key:
            logger.error("NewsAPI not configured")
            return []
        
        try:
            params = {
                'category': category,
                'language': language,
                'apiKey': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/top-headlines/sources", params=params)
                response.raise_for_status()
                
                data = response.json()
                sources = data.get('sources', [])
                
                logger.info(f"NewsAPI found {len(sources)} sources for category: {category}")
                return sources
            
        except httpx.HTTPError as e:
            logger.error(f"NewsAPI sources HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"NewsAPI sources error: {e}")
            return []
    
    async def search_articles_by_domain(self, domain: str, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for articles from a specific domain."""
        
        if not self.api_key:
            logger.error("NewsAPI not configured")
            return []
        
        try:
            search_query = f"{query} domain:{domain}" if query else f"domain:{domain}"
            
            params = {
                'q': search_query,
                'pageSize': min(100, max_results),
                'apiKey': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/everything", params=params)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get('articles', [])
                
                logger.info(f"NewsAPI found {len(articles)} articles from domain: {domain}")
                return articles[:max_results]
            
        except httpx.HTTPError as e:
            logger.error(f"NewsAPI domain search HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"NewsAPI domain search error: {e}")
            return []