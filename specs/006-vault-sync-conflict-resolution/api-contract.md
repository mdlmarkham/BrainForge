# Conflict Resolution API Contract Specification

## API Endpoints Overview

### Base Path: `/api/v1/conflicts`

All endpoints require authentication and return JSON responses.

## 1. Conflict Detection Endpoints

### 1.1 Detect Conflicts

**Endpoint:** `POST /api/v1/conflicts/detect`

**Description:** Perform comprehensive conflict detection analysis across the vault.

**Request Body:**
```json
{
  "sync_config": {
    "direction": "bidirectional",
    "conflict_resolution": "semantic_merge",
    "dry_run": false,
    "incremental": true
  },
  "analysis_depth": "standard",
  "include_semantic": true,
  "include_structural": true,
  "force_reanalysis": false
}
```

**Response (200):**
```json
{
  "success": true,
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-11-30T21:00:00Z",
  "total_notes_analyzed": 1500,
  "conflicts_detected": 23,
  "conflicts_by_severity": {
    "low": 15,
    "medium": 6,
    "high": 2,
    "critical": 0
  },
  "conflicts_by_type": {
    "content": 18,
    "metadata": 3,
    "structural": 2
  },
  "processing_time": 12.5,
  "cache_hit_ratio": 0.85,
  "recommended_actions": [
    {
      "action": "auto_resolve_low_severity",
      "conflicts_count": 15,
      "estimated_time": "2 minutes"
    }
  ]
}
```

### 1.2 Get Conflict Details

**Endpoint:** `GET /api/v1/conflicts/{conflict_id}`

**Description:** Retrieve detailed analysis for a specific conflict.

**Response (200):**
```json
{
  "success": true,
  "conflict": {
    "conflict_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "note_id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
    "timestamp": "2025-11-30T21:00:00Z",
    "conflict_type": "content",
    "severity": "medium",
    "content_analysis": {
      "content_similarity": 0.75,
      "change_significance": "reorganization",
      "intent_preservation_score": 0.92,
      "added_content": "## New Section\\n\\nAdditional research findings...",
      "removed_content": "Outdated reference to previous study"
    },
    "metadata_analysis": {
      "conflicts": [],
      "critical_conflicts": []
    },
    "structural_analysis": {
      "link_conflicts": {
        "added_links": ["[[Related Note]]"],
        "removed_links": []
      }
    },
    "auto_resolution_available": true,
    "recommended_strategy": "semantic_merge",
    "user_intervention_required": false
  }
}
```

## 2. Conflict Resolution Endpoints

### 2.1 Resolve Conflict

**Endpoint:** `POST /api/v1/conflicts/{conflict_id}/resolve`

**Description:** Apply a resolution strategy to a specific conflict.

**Request Body:**
```json
{
  "resolution_strategy": "semantic_merge",
  "user_notes": "Merging research findings from both versions",
  "apply_to_all_similar": false,
  "create_backup": true
}
```

**Response (200):**
```json
{
  "success": true,
  "resolution_id": "c3d4e5f6-g7h8-9012-cdef-g34567890123",
  "timestamp": "2025-11-30T21:05:00Z",
  "conflict_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "applied_strategy": "semantic_merge",
  "resolution_effectiveness": 0.95,
  "resolved_note": {
    "id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
    "content": "Merged content with semantic preservation...",
    "version": 5
  },
  "backup_created": true,
  "version_history_entry": {
    "id": "d4e5f6g7-h8i9-0123-defg-h45678901234",
    "version": 5,
    "change_reason": "Semantic merge of conflicting edits"
  }
}
```

### 2.2 Batch Conflict Resolution

**Endpoint:** `POST /api/v1/conflicts/resolve/batch`

**Description:** Resolve multiple conflicts with a single strategy.

**Request Body:**
```json
{
  "conflict_ids": [
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "b2c3d4e5-f6g7-8901-bcde-f23456789012"
  ],
  "resolution_strategy": "keep_brainforge",
  "create_backup": true
}
```

**Response (200):**
```json
{
  "success": true,
  "batch_id": "e5f6g7h8-i9j0-1234-efgh-i56789012345",
  "timestamp": "2025-11-30T21:10:00Z",
  "results": [
    {
      "conflict_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "success": true,
      "resolution_effectiveness": 1.0
    },
    {
      "conflict_id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
      "success": true,
      "resolution_effectiveness": 1.0
    }
  ],
  "summary": {
    "total_conflicts": 2,
    "successful_resolutions": 2,
    "failed_resolutions": 0,
    "average_effectiveness": 1.0
  }
}
```

## 3. Configuration Endpoints

### 3.1 Get Conflict Detection Configuration

**Endpoint:** `GET /api/v1/conflicts/config`

**Response (200):**
```json
{
  "success": true,
  "config": {
    "enable_semantic_analysis": true,
    "enable_structural_analysis": true,
    "semantic_analysis_threshold": 0.8,
    "content_similarity_threshold": 0.9,
    "max_concurrent_analyses": 10,
    "cache_ttl_seconds": 3600,
    "minimum_confidence": 0.7,
    "require_manual_review": false,
    "manual_review_threshold": 0.3
  }
}
```

### 3.2 Update Conflict Detection Configuration

**Endpoint:** `PUT /api/v1/conflicts/config`

**Request Body:**
```json
{
  "enable_semantic_analysis": true,
  "semantic_analysis_threshold": 0.85,
  "max_concurrent_analyses": 15
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "updated_fields": [
    "semantic_analysis_threshold",
    "max_concurrent_analyses"
  ]
}
```

## 4. Monitoring and Analytics Endpoints

### 4.1 Get Conflict Statistics

**Endpoint:** `GET /api/v1/conflicts/statistics`

**Query Parameters:**
- `time_range` (optional): "24h", "7d", "30d", "all"
- `severity_filter` (optional): "low", "medium", "high", "critical"

**Response (200):**
```json
{
  "success": true,
  "statistics": {
    "time_range": "7d",
    "total_conflicts": 150,
    "conflicts_by_severity": {
      "low": 110,
      "medium": 30,
      "high": 8,
      "critical": 2
    },
    "resolution_success_rate": 0.98,
    "average_resolution_time": "45 seconds",
    "most_common_conflict_type": "content",
    "user_intervention_rate": 0.15
  },
  "trends": {
    "conflicts_per_day": [20, 25, 18, 22, 30, 25, 10],
    "auto_resolution_rate": [0.95, 0.92, 0.98, 0.96, 0.94, 0.97, 0.99]
  }
}
```

### 4.2 Get Performance Metrics

**Endpoint:** `GET /api/v1/conflicts/metrics`

**Response (200):**
```json
{
  "success": true,
  "metrics": {
    "detection_performance": {
      "average_analysis_time": "12.5 seconds",
      "cache_hit_rate": 0.85,
      "concurrent_analyses": 8,
      "memory_usage": "256 MB"
    },
    "resolution_performance": {
      "average_resolution_time": "45 seconds",
      "success_rate": 0.98,
      "backup_creation_time": "5 seconds"
    },
    "system_health": {
      "database_connections": 12,
      "queue_length": 3,
      "last_health_check": "2025-11-30T21:00:00Z"
    }
  }
}
```

## 5. Error Responses

### Common Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "error": "invalid_configuration",
  "message": "Invalid analysis depth specified",
  "details": {
    "field": "analysis_depth",
    "expected_values": ["quick", "standard", "deep"]
  }
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": "conflict_not_found",
  "message": "Conflict with ID a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found"
}
```

**409 Conflict:**
```json
{
  "success": false,
  "error": "resolution_conflict",
  "message": "Cannot resolve conflict - manual intervention required",
  "details": {
    "conflict_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "reason": "Critical metadata conflict detected"
  }
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": "internal_error",
  "message": "Unexpected error during conflict analysis",
  "request_id": "req-1234567890"
}
```

## 6. Webhook Events

### 6.1 Conflict Detection Complete

**Event:** `conflict.detection.complete`

**Payload:**
```json
{
  "event_type": "conflict.detection.complete",
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-11-30T21:00:00Z",
  "results": {
    "total_notes_analyzed": 1500,
    "conflicts_detected": 23,
    "processing_time": 12.5
  },
  "next_actions": [
    {
      "action": "review_conflicts",
      "url": "/api/v1/conflicts/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  ]
}
```

### 6.2 Conflict Resolution Complete

**Event:** `conflict.resolution.complete`

**Payload:**
```json
{
  "event_type": "conflict.resolution.complete",
  "resolution_id": "c3d4e5f6-g7h8-9012-cdef-g34567890123",
  "timestamp": "2025-11-30T21:05:00Z",
  "results": {
    "conflict_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "strategy_used": "semantic_merge",
    "effectiveness": 0.95,
    "backup_created": true
  }
}
```

## 7. Rate Limiting

- **Detection endpoints**: 10 requests per minute per user
- **Resolution endpoints**: 5 requests per minute per user
- **Configuration endpoints**: 2 requests per minute per user
- **Monitoring endpoints**: 20 requests per minute per user

## 8. Authentication

All endpoints require Bearer token authentication:
```
Authorization: Bearer <jwt_token>
```

## 9. Versioning

- Current API version: v1
- Version specified in URL path
- Backward compatibility maintained within major versions
- Deprecated endpoints will have 6-month sunset period

This API contract provides a comprehensive interface for managing conflict detection and resolution while maintaining performance, security, and usability standards.