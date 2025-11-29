"""HNSW indexing service for approximate nearest neighbor search.

This service manages HNSW (Hierarchical Navigable Small World) index
configuration, optimization, and search operations for efficient
vector similarity search.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
import asyncio
from datetime import datetime

from src.config.database import db_config
from src.models.embedding import Embedding
from src.services.database import DatabaseService


logger = logging.getLogger(__name__)


class HNSWIndex:
    """Service for HNSW index management and optimization."""
    
    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        
        # HNSW index configuration parameters
        self.default_config = {
            "m": 16,           # Number of bi-directional links per element
            "ef_construction": 64,  # Size of dynamic candidate list during construction
            "ef_search": 40,   # Size of dynamic candidate list during search
            "distance_metric": "cosine"  # Default distance metric
        }
        
        # Performance tuning parameters
        self.performance_configs = {
            "high_precision": {"m": 24, "ef_construction": 100, "ef_search": 80},
            "balanced": {"m": 16, "ef_construction": 64, "ef_search": 40},
            "high_speed": {"m": 12, "ef_construction": 40, "ef_search": 20}
        }
    
    async def create_index(self, config: Dict[str, Any] = None) -> bool:
        """Create HNSW index on the embeddings table.
        
        Args:
            config: HNSW index configuration parameters
            
        Returns:
            True if index creation successful, False otherwise
        """
        try:
            index_config = config or self.default_config
            
            # Validate configuration
            if not self._validate_index_config(index_config):
                logger.error("Invalid HNSW index configuration")
                return False
            
            success = await self.database_service.create_hnsw_index(
                index_name="embeddings_hnsw_idx",
                column_name="vector",
                config=index_config
            )
            
            if success:
                logger.info("HNSW index created successfully")
            else:
                logger.error("HNSW index creation failed")
            
            return success
            
        except Exception as e:
            logger.error(f"HNSW index creation failed: {e}")
            return False
    
    async def optimize_index(self, config: Dict[str, Any] = None) -> bool:
        """Optimize HNSW index for current data distribution.
        
        Args:
            config: Optimization configuration
            
        Returns:
            True if optimization successful, False otherwise
        """
        try:
            # Get current index statistics
            stats = await self.get_index_statistics()
            if not stats:
                logger.warning("No index statistics available for optimization")
                return False
            
            # Determine optimal configuration based on data characteristics
            optimal_config = self._calculate_optimal_config(stats, config)
            
            # Rebuild index with optimal configuration
            success = await self.rebuild_index(optimal_config)
            
            if success:
                logger.info("HNSW index optimized successfully")
            else:
                logger.warning("HNSW index optimization may not have completed fully")
            
            return success
            
        except Exception as e:
            logger.error(f"HNSW index optimization failed: {e}")
            return False
    
    async def rebuild_index(self, config: Dict[str, Any] = None) -> bool:
        """Rebuild HNSW index with new configuration.
        
        Args:
            config: New index configuration
            
        Returns:
            True if rebuild successful, False otherwise
        """
        try:
            # Drop existing index
            drop_success = await self.database_service.drop_index("embeddings_hnsw_idx")
            if not drop_success:
                logger.warning("Failed to drop existing HNSW index")
            
            # Create new index
            create_success = await self.create_index(config)
            return create_success
            
        except Exception as e:
            logger.error(f"HNSW index rebuild failed: {e}")
            return False
    
    async def get_index_statistics(self) -> Optional[Dict[str, Any]]:
        """Get statistics about the HNSW index.
        
        Returns:
            Dictionary with index statistics or None if unavailable
        """
        try:
            stats = await self.database_service.get_index_statistics("embeddings_hnsw_idx")
            return stats
        except Exception as e:
            logger.error(f"Failed to get HNSW index statistics: {e}")
            return None
    
    async def search_with_hnsw(self, query_vector: List[float], 
                              k: int = 10,
                              ef_search: int = None,
                              distance_metric: str = "cosine") -> List[Tuple[Embedding, float]]:
        """Perform approximate nearest neighbor search using HNSW index.
        
        Args:
            query_vector: Query vector for similarity search
            k: Number of nearest neighbors to return
            ef_search: Size of dynamic candidate list (overrides default)
            distance_metric: Distance metric to use
            
        Returns:
            List of (embedding, distance) tuples
        """
        try:
            # Use provided ef_search or default
            search_ef = ef_search or self.default_config["ef_search"]
            
            results = await self.database_service.hnsw_search(
                query_vector=query_vector,
                k=k,
                ef_search=search_ef,
                distance_metric=distance_metric
            )
            
            logger.debug(f"HNSW search returned {len(results)} results with ef_search={search_ef}")
            return results
            
        except Exception as e:
            logger.error(f"HNSW search failed: {e}")
            return []
    
    async def batch_hnsw_search(self, query_vectors: List[List[float]],
                               k: int = 10,
                               ef_search: int = None) -> List[List[Tuple[Embedding, float]]]:
        """Perform batch approximate nearest neighbor search.
        
        Args:
            query_vectors: List of query vectors
            k: Number of nearest neighbors per query
            ef_search: Size of dynamic candidate list
            
        Returns:
            List of results for each query vector
        """
        valid_vectors = [vec for vec in query_vectors if self._validate_vector(vec)]
        if not valid_vectors:
            return []
        
        try:
            # Process queries in parallel
            tasks = []
            for query_vector in valid_vectors:
                task = self.search_with_hnsw(
                    query_vector=query_vector,
                    k=k,
                    ef_search=ef_search
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch HNSW search task failed: {result}")
                    valid_results.append([])
                else:
                    valid_results.append(result)
            
            logger.info(f"Batch HNSW search processed {len(valid_vectors)} queries")
            return valid_results
            
        except Exception as e:
            logger.error(f"Batch HNSW search failed: {e}")
            return [[] for _ in valid_vectors]
    
    async def tune_index_parameters(self, sample_queries: List[List[float]],
                                   target_recall: float = 0.95) -> Dict[str, Any]:
        """Tune HNSW parameters for optimal performance and recall.
        
        Args:
            sample_queries: Sample query vectors for parameter tuning
            target_recall: Target recall rate for tuning
            
        Returns:
            Optimized index configuration
        """
        try:
            if not sample_queries:
                logger.warning("No sample queries provided for parameter tuning")
                return self.default_config
            
            # Test different configurations
            best_config = self.default_config
            best_score = 0.0
            
            for config_name, config in self.performance_configs.items():
                # Rebuild index with test configuration
                await self.rebuild_index(config)
                
                # Measure performance and recall
                score = await self._evaluate_configuration(sample_queries, config, target_recall)
                
                if score > best_score:
                    best_score = score
                    best_config = config
            
            logger.info(f"Best HNSW configuration: {best_config} with score {best_score:.3f}")
            return best_config
            
        except Exception as e:
            logger.error(f"HNSW parameter tuning failed: {e}")
            return self.default_config
    
    async def _evaluate_configuration(self, sample_queries: List[List[float]],
                                    config: Dict[str, Any],
                                    target_recall: float) -> float:
        """Evaluate a configuration by measuring performance and recall."""
        try:
            # Measure search performance
            start_time = asyncio.get_event_loop().time()
            
            results = await self.batch_hnsw_search(
                query_vectors=sample_queries,
                k=10,
                ef_search=config.get("ef_search", 40)
            )
            
            end_time = asyncio.get_event_loop().time()
            avg_response_time = (end_time - start_time) / len(sample_queries) if sample_queries else 0
            
            # Calculate recall (this would need ground truth for proper evaluation)
            # For now, use a simplified metric based on result quality
            recall_metric = self._calculate_recall_metric(results)
            
            # Combine metrics into a single score
            performance_score = max(0, 1.0 - (avg_response_time / 1.0))  # Normalize to 1 second
            recall_score = min(1.0, recall_metric / target_recall)
            
            # Weighted combination (adjust weights based on requirements)
            final_score = 0.6 * recall_score + 0.4 * performance_score
            
            return final_score
            
        except Exception as e:
            logger.error(f"Configuration evaluation failed: {e}")
            return 0.0
    
    def _calculate_recall_metric(self, results: List[List[Tuple[Embedding, float]]]) -> float:
        """Calculate a simplified recall metric for configuration evaluation."""
        if not results:
            return 0.0
        
        total_results = 0
        valid_results = 0
        
        for query_results in results:
            total_results += len(query_results)
            # Count results with reasonable distance scores
            valid_results += sum(1 for _, distance in query_results if distance < 0.8)
        
        if total_results == 0:
            return 0.0
        
        return valid_results / total_results
    
    def _validate_index_config(self, config: Dict[str, Any]) -> bool:
        """Validate HNSW index configuration parameters."""
        required_params = ["m", "ef_construction", "ef_search", "distance_metric"]
        
        for param in required_params:
            if param not in config:
                logger.error(f"Missing required HNSW parameter: {param}")
                return False
        
        # Validate parameter ranges
        m = config["m"]
        if not (4 <= m <= 48):
            logger.error(f"Invalid m parameter: {m} (must be between 4 and 48)")
            return False
        
        ef_construction = config["ef_construction"]
        if not (10 <= ef_construction <= 200):
            logger.error(f"Invalid ef_construction: {ef_construction} (must be between 10 and 200)")
            return False
        
        ef_search = config["ef_search"]
        if not (10 <= ef_search <= 200):
            logger.error(f"Invalid ef_search: {ef_search} (must be between 10 and 200)")
            return False
        
        distance_metric = config["distance_metric"]
        if distance_metric not in ["cosine", "l2", "inner_product"]:
            logger.error(f"Unsupported distance metric: {distance_metric}")
            return False
        
        return True
    
    def _validate_vector(self, vector: List[float]) -> bool:
        """Validate that a vector meets requirements."""
        if not vector or len(vector) != 1536:
            return False
        
        for value in vector:
            if not isinstance(value, (int, float)) or not (-10 <= value <= 10):
                return False
        
        return True
    
    def _calculate_optimal_config(self, stats: Dict[str, Any], user_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate optimal HNSW configuration based on data statistics."""
        if user_config:
            return user_config
        
        # Simple heuristic based on dataset size
        dataset_size = stats.get("total_vectors", 0)
        
        if dataset_size < 1000:
            # Small dataset - prioritize speed
            return self.performance_configs["high_speed"]
        elif dataset_size < 10000:
            # Medium dataset - balanced approach
            return self.performance_configs["balanced"]
        else:
            # Large dataset - prioritize precision
            return self.performance_configs["high_precision"]
    
    async def monitor_index_performance(self) -> Dict[str, Any]:
        """Monitor HNSW index performance and health."""
        try:
            stats = await self.get_index_statistics()
            if not stats:
                return {"status": "unknown", "message": "No statistics available"}
            
            # Analyze index health
            index_size = stats.get("index_size_mb", 0)
            build_time = stats.get("build_time_seconds", 0)
            query_performance = stats.get("avg_query_time_ms", 0)
            
            health_status = "healthy"
            messages = []
            
            if index_size > 1000:  # 1GB threshold
                health_status = "warning"
                messages.append("Index size exceeds 1GB - consider optimization")
            
            if query_performance > 500:  # 500ms threshold
                health_status = "warning"
                messages.append("Query performance below target - consider tuning")
            
            return {
                "status": health_status,
                "index_size_mb": index_size,
                "build_time_seconds": build_time,
                "avg_query_time_ms": query_performance,
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"Index performance monitoring failed: {e}")
            return {"status": "error", "message": str(e)}


class MockHNSWIndex(HNSWIndex):
    """Mock HNSW index for testing without database dependency."""
    
    def __init__(self, database_service: DatabaseService):
        super().__init__(database_service)
        self._index_created = False
    
    async def create_index(self, config: Dict[str, Any] = None) -> bool:
        """Mock index creation."""
        self._index_created = True
        logger.info("Mock HNSW index created")
        return True
    
    async def search_with_hnsw(self, query_vector: List[float], 
                              k: int = 10,
                              ef_search: int = None,
                              distance_metric: str = "cosine") -> List[Tuple[Embedding, float]]:
        """Mock HNSW search."""
        if not self._index_created:
            logger.warning("HNSW index not created - returning empty results")
            return []
        
        # Return mock results
        return []  # Simplified for testing


# Factory function to create appropriate HNSW index
def create_hnsw_index(database_service: DatabaseService, use_mock: bool = False) -> HNSWIndex:
    """Create an HNSW index instance.
    
    Args:
        database_service: Database service instance
        use_mock: Whether to use mock index (for testing)
        
    Returns:
        HNSW index instance
    """
    if use_mock:
        return MockHNSWIndex(database_service)
    else:
        return HNSWIndex(database_service)