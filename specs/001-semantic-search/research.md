# Research Document: Semantic Search Pipeline

**Feature**: Semantic Search Pipeline  
**Branch**: `001-semantic-search`  
**Date**: 2025-11-28  
**Plan**: [plan.md](plan.md)  
**Spec**: [spec.md](spec.md)

## Research Tasks

Based on the technical context and constitutional requirements, the following research areas need investigation for the semantic search pipeline:

### 1. PGVector Integration and Performance Optimization
**Context**: Need efficient vector storage and retrieval with PostgreSQL/PGVector for semantic search

**Research Questions**:
- What are the optimal PGVector index types (HNSW vs IVFFlat) for semantic search workloads?
- How to configure vector dimensions and index parameters for 10k-100k note scale?
- What are the performance characteristics of hybrid search (vector + metadata filtering)?

### 2. Embedding Model Selection and Management
**Context**: Need consistent embedding model with version tracking and performance characteristics

**Research Questions**:
- Which embedding models provide optimal balance of quality, performance, and dimension size?
- How to implement embedding model versioning and migration strategies?
- What are the best practices for embedding generation and caching?

### 3. Hybrid Search Algorithm Design
**Context**: Need to combine semantic similarity with metadata filtering for effective search

**Research Questions**:
- What are effective ranking algorithms for combining vector similarity and metadata relevance?
- How to implement tunable hybrid search with configurable weighting?
- What are the performance implications of different hybrid search strategies?

### 4. Search API Design and Contract Testing
**Context**: Need well-defined search interfaces with constitutional compliance

**Research Questions**:
- What are the optimal API patterns for hybrid search with flexible filtering?
- How to design search contracts that support both human and agent usage?
- What are the best practices for search result pagination and relevance scoring?

## Research Findings

### PGVector Integration and Performance Optimization

**Decision**: Use HNSW index for semantic search with configurable parameters and hybrid search capabilities

**Rationale**:
- HNSW provides better query performance for approximate nearest neighbor search
- Supports constitutional performance requirements (<500ms for 10k notes)
- Configurable parameters allow tuning for different dataset sizes
- PostgreSQL integration ensures ACID compliance for constitutional data integrity
- Hybrid search combining vector similarity with metadata filtering supports progressive enhancement

**Implementation Details from Context7 Research**:

**HNSW Index Configuration**:
```sql
-- Create HNSW index for semantic search
CREATE INDEX ON embeddings USING hnsw (vector vector_l2_ops)
WITH (m = 16, ef_construction = 64, ef_search = 40);
```

**Hybrid Search Implementation**:
```sql
-- Combine vector search with metadata filtering
SELECT id, content, embedding <-> '[0.3,0.4,0.5,0.6,0.7]' AS distance
FROM notes
WHERE metadata->>'category' = 'tutorial'
ORDER BY distance
LIMIT 5;

-- Multi-column filter with vector search
SELECT id, content FROM notes
WHERE tags @> ARRAY['ai', 'research'] AND created_at > '2024-01-01'
ORDER BY embedding <-> '[0.2,0.3,0.4,0.5,0.6]'
LIMIT 10;
```

**Distance Metrics Support**:
- L2 distance (Euclidean): `embedding <-> query_vector`
- Cosine distance: `embedding <=> query_vector` (best for normalized vectors)
- Inner product: `embedding <#> query_vector` (for OpenAI embeddings)

**Performance Benchmarks Needed**:
- Query latency measurements at 1k, 10k, 50k note scales
- Index build time and storage requirements
- Hybrid search performance with metadata filtering
- Distance metric comparison for different embedding types

### Embedding Model Selection and Management

**Decision**: Use OpenAI text-embedding-3-small model (1536 dimensions) with version tracking

**Rationale**:
- 1536 dimensions provide good quality with reasonable storage requirements
- OpenAI API provides consistent embedding quality and performance
- Version tracking supports constitutional AI governance requirements
- Fallback mechanisms available for API unavailability

**Implementation Details from Context7 Research**:

**OpenAI Embedding Generation**:
```python
from openai import OpenAI

client = OpenAI()

# Single text embedding
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="The quick brown fox jumps over the lazy dog",
)
embedding_vector = response.data[0].embedding
print(f"Embedding dimensions: {len(embedding_vector)}")

# Multiple texts with custom dimensions
response = client.embeddings.create(
    model="text-embedding-3-large",
    input=["First text", "Second text", "Third text"],
    dimensions=256,
    encoding_format="float",
)
```

**Error Handling and Fallback**:
```python
try:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text_content,
    )
    embedding = response.data[0].embedding
except Exception as e:
    # Fallback to metadata-only search or cached embeddings
    logger.error(f"Embedding generation failed: {e}")
    return None
```

**Implementation Strategy**:
- Embedding metadata stored with each note (model name, version, timestamp)
- Background job for embedding regeneration on model updates
- Caching layer for frequently accessed embeddings
- Fallback to metadata-only search during embedding service outages
- Batch processing for multiple notes to optimize API usage

### Hybrid Search Algorithm Design

**Decision**: Implement weighted combination of vector similarity and metadata relevance

**Rationale**:
- Supports constitutional requirement for progressive enhancement (metadata-only search available)
- Tunable weights allow optimization for different use cases
- Provides flexibility for both semantic and structured search needs
- Maintains performance within constitutional constraints

**Algorithm Design**:
```python
# Hybrid score = α * semantic_score + β * metadata_score
# where α + β = 1, configurable per query
```

**Ranking Factors**:
- Semantic similarity (cosine distance from query embedding)
- Metadata relevance (tag matches, note type, recency)
- Link graph centrality (future enhancement)
- User interaction patterns (future enhancement)

### Search API Design and Contract Testing

**Decision**: RESTful API with flexible filtering and pagination support using FastAPI

**Rationale**:
- RESTful design supports constitutional requirement for well-defined interfaces
- Flexible filtering enables both human and agent usage patterns
- Pagination ensures performance with large result sets
- Contract testing validates constitutional compliance
- FastAPI provides automatic OpenAPI documentation and validation

**Implementation Details from Context7 Research**:

**FastAPI Endpoint Implementation**:
```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    semantic_weight: float = 0.7
    metadata_weight: float = 0.3
    limit: int = 10
    offset: int = 0

class SearchResponse(BaseModel):
    results: List[dict]
    total_count: int
    query_id: str
    response_time_ms: int

@app.post("/search", response_model=SearchResponse)
async def search_hybrid(request: SearchRequest):
    """Perform hybrid search combining semantic and metadata components."""
    try:
        # Validate weights sum to 1.0
        if abs(request.semantic_weight + request.metadata_weight - 1.0) > 0.001:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Semantic and metadata weights must sum to 1.0"
            )
        
        # Implement search logic
        results = await search_service.hybrid_search(request)
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search parameters: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )
```

**Error Handling Patterns**:
```python
# Custom error responses for different scenarios
@app.get("/search/semantic")
async def search_semantic(query: str, limit: int = 10):
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    # Semantic search implementation
    results = await search_service.semantic_search(query, limit)
    return results
```

**API Endpoints**:
- `POST /search` - Hybrid search with query text and filters
- `GET /search/semantic` - Semantic-only search
- `GET /search/metadata` - Metadata-only search

**Search Request Schema**:
```json
{
  "query": "text query",
  "filters": {
    "tags": ["tag1", "tag2"],
    "note_type": "literature",
    "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
  },
  "semantic_weight": 0.7,
  "metadata_weight": 0.3,
  "limit": 10,
  "offset": 0
}
```

## Technical Decisions Summary

| Component | Decision | Constitutional Alignment | Validation Needed |
|-----------|----------|--------------------------|-------------------|
| Vector Index | HNSW with configurable parameters | ✅ Performance benchmarks | Query latency at scale |
| Embedding Model | OpenAI text-embedding-3-small | ✅ Version tracking | Quality vs performance tradeoffs |
| Hybrid Search | Weighted combination algorithm | ✅ Progressive enhancement | Ranking quality assessment |
| API Design | RESTful with flexible filtering | ✅ Well-defined interfaces | Contract testing coverage |

## Implementation Guidelines

1. **Performance First**: Implement and benchmark search performance before adding advanced features
2. **Contract Testing**: Write search API contract tests before implementation
3. **Progressive Enhancement**: Ensure metadata-only search works reliably before semantic features
4. **Monitoring**: Implement search performance monitoring and quality metrics
5. **Caching**: Add embedding and result caching for frequently accessed data

## Risk Mitigation Strategy

### High-Priority Risks
1. **Search Performance**: Implement performance monitoring and index optimization strategies
2. **Embedding Service Reliability**: Design fallback mechanisms and caching layers
3. **Ranking Quality**: Implement A/B testing for search result relevance
4. **Scale Performance**: Plan indexing strategies for larger datasets

### Validation Experiments Required
1. **Performance Benchmarking**: Measure search latency at different dataset sizes
2. **Quality Assessment**: Human evaluation of search result relevance
3. **Fallback Testing**: Verify metadata-only search functionality during outages
4. **Integration Testing**: End-to-end search workflow validation

## Next Steps

1. **Begin Implementation**: Start with core search service and API endpoints
2. **Performance Testing**: Establish baseline performance metrics
3. **Quality Validation**: Implement search relevance assessment
4. **Documentation**: Create search API documentation and usage guides

The semantic search pipeline builds upon the established constitutional foundation while adding critical AI-enhanced capabilities with proper validation and oversight.