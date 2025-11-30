"""Caching service for performance optimization in BrainForge."""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional, TypeVar
from uuid import UUID

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheService:
    """Redis-based caching service for performance optimization."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache service.
        
        Args:
            redis_url: Redis connection URL. If None, uses REDIS_URL env var.
        """
        self.redis_url = redis_url
        self.redis_client: Optional[Redis] = None
        self._connection_lock = asyncio.Lock()
    
    async def get_client(self) -> Redis:
        """Get Redis client with lazy initialization."""
        if self.redis_client is None:
            async with self._connection_lock:
                if self.redis_client is None:  # Double-check locking
                    redis_url = self.redis_url or "redis://localhost:6379"
                    self.redis_client = Redis.from_url(
                        redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
        return self.redis_client
    
    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = 3600  # Default 1 hour
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire_seconds: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value, default=str)
            
            if expire_seconds:
                await client.setex(key, expire_seconds, serialized_value)
            else:
                await client.set(key, serialized_value)
            
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache key {key}: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            client = await self.get_client()
            serialized_value = await client.get(key)
            
            if serialized_value is None:
                return default
            
            return json.loads(serialized_value)
        except Exception as e:
            logger.warning(f"Failed to get cache key {key}: {e}")
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Failed to check cache key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None


class CacheManager:
    """High-level cache manager with domain-specific caching strategies."""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        
        # Cache configuration for different data types
        self.cache_config = {
            "user": {"ttl": 3600},  # 1 hour
            "note": {"ttl": 1800},  # 30 minutes
            "search": {"ttl": 300},  # 5 minutes
            "research": {"ttl": 900},  # 15 minutes
            "metrics": {"ttl": 60},  # 1 minute
        }
    
    def _get_cache_key(self, domain: str, identifier: str) -> str:
        """Generate cache key for domain and identifier.
        
        Args:
            domain: Data domain (user, note, etc.)
            identifier: Unique identifier
            
        Returns:
            Cache key
        """
        return f"{domain}:{identifier}"
    
    async def cache_user(self, user_id: UUID, user_data: dict) -> bool:
        """Cache user data.
        
        Args:
            user_id: User ID
            user_data: User data to cache
            
        Returns:
            True if successful
        """
        key = self._get_cache_key("user", str(user_id))
        ttl = self.cache_config["user"]["ttl"]
        return await self.cache_service.set(key, user_data, ttl)
    
    async def get_cached_user(self, user_id: UUID) -> Optional[dict]:
        """Get cached user data.
        
        Args:
            user_id: User ID
            
        Returns:
            Cached user data or None
        """
        key = self._get_cache_key("user", str(user_id))
        return await self.cache_service.get(key)
    
    async def cache_note(self, note_id: UUID, note_data: dict) -> bool:
        """Cache note data.
        
        Args:
            note_id: Note ID
            note_data: Note data to cache
            
        Returns:
            True if successful
        """
        key = self._get_cache_key("note", str(note_id))
        ttl = self.cache_config["note"]["ttl"]
        return await self.cache_service.set(key, note_data, ttl)
    
    async def get_cached_note(self, note_id: UUID) -> Optional[dict]:
        """Get cached note data.
        
        Args:
            note_id: Note ID
            
        Returns:
            Cached note data or None
        """
        key = self._get_cache_key("note", str(note_id))
        return await self.cache_service.get(key)
    
    async def cache_search_results(self, query: str, results: list) -> bool:
        """Cache search results.
        
        Args:
            query: Search query
            results: Search results to cache
            
        Returns:
            True if successful
        """
        # Normalize query for cache key
        normalized_query = query.lower().strip()
        key = self._get_cache_key("search", normalized_query)
        ttl = self.cache_config["search"]["ttl"]
        return await self.cache_service.set(key, results, ttl)
    
    async def get_cached_search_results(self, query: str) -> Optional[list]:
        """Get cached search results.
        
        Args:
            query: Search query
            
        Returns:
            Cached search results or None
        """
        normalized_query = query.lower().strip()
        key = self._get_cache_key("search", normalized_query)
        return await self.cache_service.get(key)
    
    async def invalidate_user_cache(self, user_id: UUID) -> bool:
        """Invalidate user cache.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        key = self._get_cache_key("user", str(user_id))
        return await self.cache_service.delete(key)
    
    async def invalidate_note_cache(self, note_id: UUID) -> bool:
        """Invalidate note cache.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if successful
        """
        key = self._get_cache_key("note", str(note_id))
        return await self.cache_service.delete(key)
    
    async def clear_domain_cache(self, domain: str) -> int:
        """Clear all cache for a domain.
        
        Args:
            domain: Data domain
            
        Returns:
            Number of keys deleted
        """
        pattern = f"{domain}:*"
        return await self.cache_service.clear_pattern(pattern)


class QueryOptimizer:
    """Query optimization service for database performance."""
    
    @staticmethod
    def optimize_note_query(filters: dict) -> dict:
        """Optimize note query filters for performance.
        
        Args:
            filters: Original query filters
            
        Returns:
            Optimized filters
        """
        optimized = filters.copy()
        
        # Add index-friendly ordering
        if "order_by" not in optimized:
            optimized["order_by"] = "created_at_desc"
        
        # Limit result size for performance
        if "limit" not in optimized:
            optimized["limit"] = 100
        
        return optimized
    
    @staticmethod
    def optimize_search_query(query: str, filters: dict) -> dict:
        """Optimize search query for performance.
        
        Args:
            query: Search query
            filters: Search filters
            
        Returns:
            Optimized search parameters
        """
        optimized = filters.copy()
        
        # Add query preprocessing
        optimized["preprocessed_query"] = query.lower().strip()
        
        # Add performance limits
        if "max_results" not in optimized:
            optimized["max_results"] = 50
        
        if "timeout_ms" not in optimized:
            optimized["timeout_ms"] = 5000  # 5 second timeout
        
        return optimized
    
    @staticmethod
    def should_use_cache(operation: str, parameters: dict) -> bool:
        """Determine if cache should be used for an operation.
        
        Args:
            operation: Operation type
            parameters: Operation parameters
            
        Returns:
            True if cache should be used
        """
        cacheable_operations = {
            "get_user": True,
            "get_note": True,
            "search_notes": parameters.get("use_cache", True),
            "get_research_metrics": True,
        }
        
        return cacheable_operations.get(operation, False)


class PerformanceMonitor:
    """Performance monitoring and optimization service."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.performance_stats = {}
    
    async def monitor_operation(
        self,
        operation: str,
        parameters: dict,
        execute_func
    ) -> Any:
        """Monitor and optimize operation execution.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            execute_func: Function to execute the operation
            
        Returns:
            Operation result
        """
        start_time = time.time()
        
        # Check if we should use cache
        if QueryOptimizer.should_use_cache(operation, parameters):
            cache_key = self._generate_cache_key(operation, parameters)
            cached_result = await self.cache_manager.cache_service.get(cache_key)
            
            if cached_result is not None:
                duration = (time.time() - start_time) * 1000
                self._record_performance(operation, True, duration)
                return cached_result
        
        # Execute the operation
        result = await execute_func()
        duration = (time.time() - start_time) * 1000
        
        # Cache the result if appropriate
        if QueryOptimizer.should_use_cache(operation, parameters):
            cache_key = self._generate_cache_key(operation, parameters)
            ttl = self._get_cache_ttl(operation)
            await self.cache_manager.cache_service.set(cache_key, result, ttl)
        
        self._record_performance(operation, False, duration)
        return result
    
    def _generate_cache_key(self, operation: str, parameters: dict) -> str:
        """Generate cache key for operation and parameters.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            
        Returns:
            Cache key
        """
        param_str = json.dumps(parameters, sort_keys=True)
        return f"operation:{operation}:{hash(param_str)}"
    
    def _get_cache_ttl(self, operation: str) -> int:
        """Get cache TTL for operation type.
        
        Args:
            operation: Operation name
            
        Returns:
            TTL in seconds
        """
        ttl_map = {
            "get_user": 3600,  # 1 hour
            "get_note": 1800,  # 30 minutes
            "search_notes": 300,  # 5 minutes
            "get_research_metrics": 60,  # 1 minute
        }
        return ttl_map.get(operation, 300)  # Default 5 minutes
    
    def _record_performance(self, operation: str, cached: bool, duration_ms: float):
        """Record operation performance.
        
        Args:
            operation: Operation name
            cached: Whether result was cached
            duration_ms: Operation duration in milliseconds
        """
        if operation not in self.performance_stats:
            self.performance_stats[operation] = {
                "total_count": 0,
                "cached_count": 0,
                "total_duration": 0,
                "average_duration": 0,
            }
        
        stats = self.performance_stats[operation]
        stats["total_count"] += 1
        stats["total_duration"] += duration_ms
        stats["average_duration"] = stats["total_duration"] / stats["total_count"]
        
        if cached:
            stats["cached_count"] += 1
    
    def get_performance_report(self) -> dict:
        """Get performance report.
        
        Returns:
            Performance statistics
        """
        return self.performance_stats


# Global cache service instance
cache_service = CacheService()
cache_manager = CacheManager(cache_service)
query_optimizer = QueryOptimizer()
performance_monitor = PerformanceMonitor(cache_manager)


def get_cache_service() -> CacheService:
    """Get cache service dependency."""
    return cache_service


def get_cache_manager() -> CacheManager:
    """Get cache manager dependency."""
    return cache_manager


def get_performance_monitor() -> PerformanceMonitor:
    """Get performance monitor dependency."""
    return performance_monitor