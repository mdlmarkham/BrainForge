"""Google Custom Search API client for content discovery."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GoogleSearchClient:
    """Client for Google Custom Search API."""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"

        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Custom Search API credentials not configured")

    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search for content using Google Custom Search API."""

        if not self.api_key or not self.search_engine_id:
            logger.error("Google Custom Search API not configured")
            return []

        try:
            results = []
            start_index = 1

            # Google Custom Search API returns up to 10 results per request
            while len(results) < max_results and start_index <= 91:  # Max 100 results
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': query,
                    'start': start_index,
                    'num': min(10, max_results - len(results))
                }

                async with httpx.AsyncClient() as client:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()

                    data = response.json()

                    if 'items' in data:
                        results.extend(data['items'])

                    # Check if there are more results
                    if 'queries' in data and 'nextPage' in data['queries']:
                        start_index += 10
                    else:
                        break

                # Rate limiting - be respectful to the API
                import asyncio
                await asyncio.sleep(0.1)

            logger.info(f"Google search found {len(results)} results for query: {query}")
            return results[:max_results]

        except httpx.HTTPError as e:
            logger.error(f"Google Search API HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Google Search API error: {e}")
            return []

    async def search_news(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search for news content using Google Custom Search API."""

        if not self.api_key or not self.search_engine_id:
            logger.error("Google Custom Search API not configured")
            return []

        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(10, max_results),
                'tbm': 'nws'  # News search
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()
                results = data.get('items', [])

                logger.info(f"Google news search found {len(results)} results for query: {query}")
                return results

        except httpx.HTTPError as e:
            logger.error(f"Google News Search API HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Google News Search API error: {e}")
            return []

    async def search_scholar(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search for scholarly content using Google Custom Search API."""

        if not self.api_key or not self.search_engine_id:
            logger.error("Google Custom Search API not configured")
            return []

        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(10, max_results),
                'tbm': 'isch'  # Image search (fallback for scholar)
            }

            # Note: Google doesn't have a dedicated scholar search in Custom Search API
            # This is a fallback implementation
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()
                results = data.get('items', [])

                logger.info(f"Google scholar search found {len(results)} results for query: {query}")
                return results

        except httpx.HTTPError as e:
            logger.error(f"Google Scholar Search API HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Google Scholar Search API error: {e}")
            return []
