# Quickstart: Researcher Agent

**Feature**: 003-researcher-agent  
**Date**: 2025-11-29

## Overview

The Researcher Agent is an AI-powered assistant that discovers, evaluates, and proposes external content for knowledge base integration with a human review workflow. It automates content discovery while maintaining constitutional compliance through human oversight.

## Prerequisites

- BrainForge system running with PostgreSQL/PGVector
- API keys for external content sources (Google Custom Search, Semantic Scholar, etc.)
- Python 3.11+ environment
- Required dependencies: FastAPI, PydanticAI, FastMCP, SpiffWorkflow

## Quick Setup

### 1. Environment Configuration

Add required API keys to your environment:

```bash
# External content discovery APIs
export GOOGLE_CSE_API_KEY=your_google_cse_key
export GOOGLE_CSE_ENGINE_ID=your_search_engine_id
export SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
export NEWS_API_KEY=your_news_api_key
```

### 2. Database Migration

Run the database migration to add researcher agent tables:

```bash
cd src
python -m cli.migrate upgrade head
```

### 3. Start the Service

Start the BrainForge API with researcher agent endpoints:

```bash
cd src
uvicorn api.main:app --reload --port 8000
```

## Basic Usage

### 1. Initiate a Research Run

```bash
curl -X POST http://localhost:8000/api/research/runs \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "machine learning interpretability",
    "parameters": {
      "sources": ["web", "academic"],
      "max_results": 20,
      "quality_threshold": 0.7
    }
  }'
```

### 2. Monitor Research Progress

```bash
# Check run status
curl http://localhost:8000/api/research/runs

# Get detailed results
curl http://localhost:8000/api/research/runs/{run_id}/sources
```

### 3. Review Proposed Content

```bash
# Get review queue
curl http://localhost:8000/api/review/queue

# Submit review decision
curl -X PATCH http://localhost:8000/api/review/queue/{item_id} \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approve",
    "notes": "High-quality source with relevant insights"
  }'
```

### 4. View Integration Proposals

```bash
# Get AI-generated integration suggestions
curl http://localhost:8000/api/integration/proposals
```

## Key Features

### Automated Content Discovery
- Discovers content from web, academic, and news sources
- Uses semantic similarity to find relevant materials
- Configurable search parameters and quality thresholds

### Quality Assessment
- Multi-factor scoring (credibility, relevance, freshness, completeness)
- AI-powered evaluation with explainable rationale
- Automatic filtering based on configurable thresholds

### Human Review Workflow
- Three-stage process: auto-filter → review queue → integration
- Configurable quality thresholds for automatic filtering
- Complete audit trails for all decisions

### Integration Suggestions
- AI-generated connections to existing knowledge
- Suggested tags and classifications
- Semantic similarity analysis

## Configuration Options

### Research Parameters
```yaml
# Default research configuration
sources: ["web", "academic", "news"]
max_results: 20
quality_threshold: 0.7
content_types: ["article", "paper", "report"]
languages: ["en"]
```

### Quality Scoring Weights
```yaml
credibility_weight: 0.4
relevance_weight: 0.3
freshness_weight: 0.15
completeness_weight: 0.15
```

### Review Workflow
```yaml
auto_reject_threshold: 0.3
auto_approve_threshold: 0.9
review_priority_cutoffs:
  high: 0.8
  medium: 0.5
  low: 0.3
```

## Monitoring and Metrics

### Performance Metrics
- Research run completion time (target: <30 minutes)
- Content discovery success rate (target: 80%)
- Quality assessment accuracy (target: 90% vs human evaluation)
- Review processing rate (target: 15+ items/hour)

### Audit Trails
- Complete record of all agent activities
- Version tracking for AI models and agents
- Decision rationale and modification history

## Troubleshooting

### Common Issues

**Research runs failing:**
- Check external API key validity
- Verify network connectivity to external services
- Review error logs for specific failure reasons

**Quality assessment inconsistencies:**
- Validate scoring weights configuration
- Check AI model version and performance
- Review evaluation rationale for insights

**Review workflow bottlenecks:**
- Adjust quality thresholds for better filtering
- Consider parallel processing for high-volume scenarios
- Monitor reviewer assignment and workload

### Debug Commands

```bash
# Check research run status
curl http://localhost:8000/api/research/runs/{run_id}

# View audit trail for specific run
# (Implementation detail - depends on audit endpoint design)

# Test external API connectivity
curl "https://www.googleapis.com/customsearch/v1?key=${GOOGLE_CSE_API_KEY}&cx=${GOOGLE_CSE_ENGINE_ID}&q=test"
```

## Next Steps

After familiarizing yourself with the basic functionality:

1. **Customize research parameters** for your specific domain
2. **Configure quality thresholds** based on your content standards  
3. **Set up scheduled research runs** for proactive discovery
4. **Integrate with existing workflows** through API calls
5. **Monitor performance metrics** and optimize configurations

The researcher agent is designed to scale from personal knowledge management to team-based curation workflows while maintaining constitutional compliance through its human review gates.