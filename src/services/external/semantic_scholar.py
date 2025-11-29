"""Semantic Scholar API client for academic content discovery."""

import os
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class SemanticScholarClient:
    """Client for Semantic Scholar API."""
    
    def __init__(self):
        self.api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        
        if not self.api_key:
            logger.warning("Semantic Scholar API key not configured")
    
    async def search_papers(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for academic papers using Semantic Scholar API."""
        
        try:
            headers = {}
            if self.api_key:
                headers['x-api-key'] = self.api_key
            
            params = {
                'query': query,
                'limit': max_results,
                'fields': 'paperId,title,abstract,url,authors,venue,year,citationCount,publicationTypes'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/paper/search", params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                papers = data.get('data', [])
                
                logger.info(f"Semantic Scholar found {len(papers)} papers for query: {query}")
                return papers
            
        except httpx.HTTPError as e:
            logger.error(f"Semantic Scholar API HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Semantic Scholar API error: {e}")
            return []
    
    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific paper."""
        
        try:
            headers = {}
            if self.api_key:
                headers['x-api-key'] = self.api_key
            
            params = {
                'fields': 'paperId,title,abstract,url,authors,venue,year,citationCount,publicationTypes,references,citations'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/paper/{paper_id}", params=params, headers=headers)
                response.raise_for_status()
                
                paper = response.json()
                return paper
            
        except httpx.HTTPError as e:
            logger.error(f"Semantic Scholar paper details HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Semantic Scholar paper details error: {e}")
            return None
    
    async def get_author_papers(self, author_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get papers by a specific author."""
        
        try:
            headers = {}
            if self.api_key:
                headers['x-api-key'] = self.api_key
            
            params = {
                'fields': 'paperId,title,abstract,url,authors,venue,year,citationCount',
                'limit': max_results
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/author/{author_id}/papers", params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                papers = data.get('data', [])
                
                logger.info(f"Found {len(papers)} papers for author {author_id}")
                return papers
            
        except httpx.HTTPError as e:
            logger.error(f"Semantic Scholar author papers HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Semantic Scholar author papers error: {e}")
            return []
    
    async def get_related_papers(self, paper_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get papers related to a specific paper."""
        
        try:
            headers = {}
            if self.api_key:
                headers['x-api-key'] = self.api_key
            
            params = {
                'fields': 'paperId,title,abstract,url,authors,venue,year,citationCount',
                'limit': max_results
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/paper/{paper_id}/citations", params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                papers = [item.get('citingPaper', {}) for item in data.get('data', [])]
                
                logger.info(f"Found {len(papers)} related papers for paper {paper_id}")
                return papers
            
        except httpx.HTTPError as e:
            logger.error(f"Semantic Scholar related papers HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Semantic Scholar related papers error: {e}")
            return []
    
    async def search_authors(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for authors using Semantic Scholar API."""
        
        try:
            headers = {}
            if self.api_key:
                headers['x-api-key'] = self.api_key
            
            params = {
                'query': query,
                'limit': max_results,
                'fields': 'authorId,name,affiliations,paperCount,citationCount'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/author/search", params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                authors = data.get('data', [])
                
                logger.info(f"Semantic Scholar found {len(authors)} authors for query: {query}")
                return authors
            
        except httpx.HTTPError as e:
            logger.error(f"Semantic Scholar author search HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Semantic Scholar author search error: {e}")
            return []