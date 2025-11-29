# Quickstart Guide: Semantic Search Pipeline

**Feature**: Semantic Search Pipeline  
**Branch**: `001-semantic-search`  
**Date**: 2025-11-28  
**Plan**: [plan.md](plan.md)  
**API**: [contracts/openapi.yaml](contracts/openapi.yaml)

## Overview

The Semantic Search Pipeline enables meaning-based retrieval of notes using embeddings and vector search, with optional hybrid search combining semantic similarity with metadata filtering.

## Prerequisites

- BrainForge API server running (port 8000)
- PostgreSQL database with PGVector extension
- OpenAI API key for embedding generation
- Existing notes in the knowledge base

## Quick Setup

### 1. Environment Configuration

```bash
# Set required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export DATABASE_URL="postgresql://user:password@localhost/brainforge"
```

### 2. Database Setup

Ensure PGVector extension is enabled:

```sql
-- Connect to your database
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. API Endpoints

The search API is available at `http://localhost:8000/api/v1/search`

## Basic Usage Examples

### Example 1: Simple Semantic Search

```bash
# Search for notes semantically similar to "machine learning"
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "machine learning algorithms",
    "limit": 10
  }'
```

**Response**:
```json
{
  "results": [
    {
      "note": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Introduction to Machine Learning",
        "content": "Machine learning is a subset of artificial intelligence...",
        "note_type": "literature",
        "tags": ["ai", "machine-learning"],
        "created_at": "2024-01-15T10:30:00Z"
      },
      "rank": 1,
      "semantic_score": 0.85,
      "metadata_score": 0.72,
      "combined_score": 0.81
    }
  ],
  "total_count": 15,
  "query_id": "456e7890-f12c-34d5-b678-901234567890",
  "response_time_ms": 125
}
```

### Example 2: Hybrid Search with Filters

```bash
# Search with metadata filters and custom weighting
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "neural networks",
    "filters": {
      "tags": ["ai", "research"],
      "note_type": "literature",
      "date_range": {
        "start": "2024-01-01",
        "end": "2024-12-31"
      }
    },
    "semantic_weight": 0.7,
    "metadata_weight": 0.3,
    "limit": 20
  }'
```

### Example 3: Semantic-Only Search

```bash
# Search using only semantic similarity
curl -X GET "http://localhost:8000/api/v1/search/semantic?query=deep%20learning&limit=5"
```

### Example 4: Metadata-Only Search

```bash
# Search using only metadata filtering
curl -X GET "http://localhost:8000/api/v1/search/metadata?tags=ai,research&note_type=literature&limit=10"
```

## Python Client Example

```python
import requests
import json

class BrainForgeSearchClient:
    def __init__(self, base_url="http://localhost:8000/api/v1", api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def hybrid_search(self, query, filters=None, semantic_weight=0.7, metadata_weight=0.3, limit=10):
        """Perform hybrid search with semantic and metadata components."""
        payload = {
            "query": query,
            "semantic_weight": semantic_weight,
            "metadata_weight": metadata_weight,
            "limit": limit
        }
        
        if filters:
            payload["filters"] = filters
        
        response = requests.post(
            f"{self.base_url}/search",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def semantic_search(self, query, limit=10):
        """Perform semantic-only search."""
        params = {"query": query, "limit": limit}
        response = requests.get(
            f"{self.base_url}/search/semantic",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def metadata_search(self, tags=None, note_type=None, limit=10):
        """Perform metadata-only search."""
        params = {"limit": limit}
        if tags:
            params["tags"] = ",".join(tags) if isinstance(tags, list) else tags
        if note_type:
            params["note_type"] = note_type
        
        response = requests.get(
            f"{self.base_url}/search/metadata",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = BrainForgeSearchClient(api_key="your-api-key")

# Hybrid search
results = client.hybrid_search(
    query="machine learning interpretability",
    filters={"tags": ["ai", "research"], "note_type": "literature"},
    semantic_weight=0.8,
    metadata_weight=0.2,
    limit=15
)

print(f"Found {results['total_count']} results")
for result in results["results"]:
    note = result["note"]
    print(f"Rank {result['rank']}: {note['title']} (score: {result['combined_score']:.3f})")
```

## Search Strategies

### 1. Semantic-Dominant Search (Default)
- Use when looking for conceptually similar content
- Higher semantic weight (0.7-0.9)
- Good for exploratory research and discovery

```python
results = client.hybrid_search(
    query="your research topic",
    semantic_weight=0.8,
    metadata_weight=0.2
)
```

### 2. Balanced Hybrid Search
- Use when you know what you're looking for
- Equal or balanced weights (0.5-0.5)
- Good for focused research with specific criteria

```python
results = client.hybrid_search(
    query="specific concept",
    filters={"tags": ["relevant-tag"], "note_type": "literature"},
    semantic_weight=0.5,
    metadata_weight=0.5
)
```

### 3. Metadata-Dominant Search
- Use for precise filtering and categorization
- Higher metadata weight (0.7-0.9)
- Good for organizational tasks and content management

```python
results = client.hybrid_search(
    query="optional text filter",
    filters={"tags": ["exact-tag"], "note_type": "specific-type"},
    semantic_weight=0.3,
    metadata_weight=0.7
)
```

## Performance Tips

### 1. Query Optimization
- Use specific, descriptive queries for better semantic matching
- Combine with relevant metadata filters to narrow results
- Start with smaller limit values for faster response times

### 2. Caching Strategy
- Frequently accessed queries benefit from caching
- Consider implementing client-side caching for repeated searches
- Monitor response times to identify performance bottlenecks

### 3. Scale Considerations
- For large knowledge bases (>10k notes), use pagination effectively
- Monitor index performance and consider index optimization
- Use appropriate HNSW index parameters for your dataset size

## Error Handling

### Common Errors and Solutions

**400 Bad Request**: Invalid search parameters
- Check parameter types and ranges
- Ensure semantic_weight + metadata_weight = 1.0
- Validate filter syntax and values

**500 Internal Server Error**: Server-side issue
- Check database connectivity
- Verify embedding service availability
- Review server logs for detailed error information

**Timeout Errors**: Performance issues
- Reduce result limit
- Simplify complex filters
- Check database performance metrics

## Monitoring and Metrics

### Key Performance Indicators
- **Response Time**: Target <500ms for 10k notes
- **Result Quality**: Human evaluation of relevance
- **Cache Hit Rate**: Effectiveness of caching strategies
- **Error Rate**: System reliability metrics

### Audit Trail
All search operations include:
- Query ID for traceability
- Execution timestamp and user/agent identifier
- Performance metrics (response time)
- Complete result set with scoring details

## Next Steps

1. **Explore API Documentation**: Visit `/docs` endpoint for interactive API exploration
2. **Test Search Quality**: Evaluate result relevance with sample queries
3. **Integrate with Applications**: Use the Python client or direct API calls
4. **Monitor Performance**: Establish baseline metrics and monitoring

The semantic search pipeline provides powerful knowledge discovery capabilities while maintaining constitutional compliance and performance standards.