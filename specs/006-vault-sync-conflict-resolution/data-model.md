# Conflict Resolution Data Model Specification

## Core Data Models

### 1. Conflict Severity Enumeration

```python
class ConflictSeverity(Enum):
    """Severity levels for detected conflicts."""
    NONE = "none"           # No conflict detected
    LOW = "low"             # Minor formatting/typo changes
    MEDIUM = "medium"       # Content reorganization
    HIGH = "high"           # Substantive content changes
    CRITICAL = "critical"   # Contradictory information
```

### 2. Conflict Type Classification

```python
class ConflictType(Enum):
    """Types of conflicts that can occur."""
    CONTENT = "content"             # Text content modifications
    METADATA = "metadata"           # Frontmatter/property changes
    STRUCTURAL = "structural"       # Link/organization changes
    MIXED = "mixed"                 # Multiple conflict types
    TEMPORAL = "temporal"           # Edit timing conflicts
```

### 3. Content Change Significance

```python
class ChangeSignificance(Enum):
    """Significance level of content changes."""
    FORMATTING = "formatting"       # Whitespace, formatting only
    MINOR_EDIT = "minor_edit"       # Spelling, grammar corrections
    REORGANIZATION = "reorganization" # Paragraph/section restructuring
    SUBSTANTIVE = "substantive"     # Content additions/deletions
    CONTRADICTORY = "contradictory" # Conflicting information
```

### 4. Resolution Strategy Options

```python
class ConflictResolutionStrategy(Enum):
    """Available conflict resolution strategies."""
    KEEP_BRAINFORGE = "keep_brainforge"     # Prefer BrainForge version
    KEEP_OBSIDIAN = "keep_obsidian"         # Prefer Obsidian version
    SEMANTIC_MERGE = "semantic_merge"       # Intelligent content merge
    MANUAL_MERGE = "manual_merge"           # Require user intervention
    CREATE_BRANCH = "create_branch"         # Create alternative version
    DEFER = "defer"                         # Postpone resolution
    SKIP = "skip"                           # Skip this conflict
```

## Primary Data Structures

### 1. ConflictData Model

```python
@dataclass
class ConflictData:
    """Comprehensive conflict detection results."""
    
    conflict_id: UUID
    note_id: UUID
    timestamp: datetime
    
    # Basic conflict information
    conflict_type: ConflictType
    severity: ConflictSeverity
    detected_by: str  # Detection method used
    
    # Source versions
    brainforge_version: NoteVersion
    obsidian_version: NoteVersion
    common_ancestor: NoteVersion | None  # For 3-way merge
    
    # Analysis results
    content_analysis: ContentConflictAnalysis
    metadata_analysis: MetadataConflictAnalysis
    structural_analysis: StructuralConflictAnalysis
    semantic_analysis: SemanticAnalysis
    
    # Resolution information
    auto_resolution_available: bool
    recommended_strategy: ConflictResolutionStrategy
    user_intervention_required: bool
    resolution_deadline: datetime | None
    
    # Audit trail
    detection_metadata: dict[str, Any]
    analysis_confidence: float  # 0.0 to 1.0
```

### 2. Content Conflict Analysis

```python
@dataclass
class ContentConflictAnalysis:
    """Detailed analysis of content conflicts."""
    
    # Basic metrics
    content_similarity: float  # 0.0 to 1.0
    change_significance: ChangeSignificance
    word_count_diff: int
    paragraph_count_diff: int
    
    # Semantic analysis
    intent_preservation_score: float  # 0.0 to 1.0
    topic_consistency: float
    conclusion_alignment: float
    
    # Change details
    added_content: str
    removed_content: str
    modified_sections: list[ContentSection]
    
    # Quality indicators
    brainforge_quality_score: float
    obsidian_quality_score: float
    merge_viability_score: float
```

### 3. Metadata Conflict Analysis

```python
@dataclass
class MetadataConflictAnalysis:
    """Analysis of metadata/frontmatter conflicts."""
    
    conflicts: list[MetadataConflict]
    critical_conflicts: list[MetadataConflict]
    non_critical_conflicts: list[MetadataConflict]
    
    # Field-level analysis
    field_changes: dict[str, FieldChange]
    consistency_issues: list[ConsistencyIssue]
    
@dataclass
class MetadataConflict:
    """Individual metadata field conflict."""
    
    field_name: str
    brainforge_value: Any
    obsidian_value: Any
    conflict_type: MetadataConflictType
    severity: ConflictSeverity
    resolution_suggestions: list[str]
    
class MetadataConflictType(Enum):
    CRITICAL_FIELD = "critical_field"      # ID, type, creation date
    PROPERTY_CONFLICT = "property_conflict" # Tag, category changes
    SCHEMA_MISMATCH = "schema_mismatch"    # Different metadata schemas
    VALIDATION_ERROR = "validation_error"  # Invalid metadata values
```

### 4. Structural Conflict Analysis

```python
@dataclass
class StructuralConflictAnalysis:
    """Analysis of note structure and link conflicts."""
    
    link_conflicts: LinkConflictAnalysis
    organization_conflicts: OrganizationConflictAnalysis
    graph_integrity_issues: list[GraphIntegrityIssue]
    
@dataclass
class LinkConflictAnalysis:
    """Analysis of internal/external link changes."""
    
    added_links: list[Link]
    removed_links: list[Link]
    modified_links: list[LinkModification]
    broken_links: list[BrokenLink]
    link_consistency_score: float
    
@dataclass
class OrganizationConflictAnalysis:
    """Analysis of note organization conflicts."""
    
    path_changes: list[PathChange]
    folder_structure_conflicts: list[FolderConflict]
    naming_conflicts: list[NamingConflict]
    organization_consistency: float
```

### 5. Semantic Analysis Model

```python
@dataclass
class SemanticAnalysis:
    """AI/LLM-based semantic conflict analysis."""
    
    # Intent analysis
    intent_preservation: IntentPreservation
    thesis_alignment: ThesisAlignment
    conclusion_consistency: ConclusionConsistency
    
    # Content quality
    coherence_score: float
    completeness_score: float
    clarity_score: float
    
    # Merge recommendations
    merge_viability: MergeViability
    suggested_merge_strategy: str
    conflict_hotspots: list[ConflictHotspot]
    
@dataclass
class IntentPreservation:
    """Analysis of whether note intent is preserved."""
    
    main_thesis_preserved: bool
    key_arguments_intact: bool
    conclusion_unchanged: bool
    overall_preservation_score: float
    preservation_confidence: float
```

## API Request/Response Models

### 1. Conflict Detection Request

```python
@dataclass
class ConflictDetectionRequest:
    """Request for conflict detection analysis."""
    
    sync_config: SyncConfig
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    include_semantic: bool = True
    include_structural: bool = True
    force_reanalysis: bool = False
    
class AnalysisDepth(Enum):
    QUICK = "quick"        # Basic timestamp/hash only
    STANDARD = "standard"  # Full analysis without LLM
    DEEP = "deep"          # Full analysis with LLM semantic
```

### 2. Conflict Detection Response

```python
@dataclass
class ConflictDetectionResponse:
    """Response from conflict detection analysis."""
    
    success: bool
    analysis_id: UUID
    timestamp: datetime
    
    # Summary statistics
    total_notes_analyzed: int
    conflicts_detected: int
    conflicts_by_severity: dict[ConflictSeverity, int]
    conflicts_by_type: dict[ConflictType, int]
    
    # Detailed results
    conflicts: list[ConflictData]
    analysis_metadata: AnalysisMetadata
    processing_time: float
    cache_hit_ratio: float
    
    # Recommendations
    recommended_actions: list[RecommendedAction]
    estimated_resolution_time: float
    risk_assessment: RiskAssessment
```

### 3. Conflict Resolution Request

```python
@dataclass
class ConflictResolutionRequest:
    """Request to resolve a specific conflict."""
    
    conflict_id: UUID
    resolution_strategy: ConflictResolutionStrategy
    user_notes: str | None = None
    apply_to_all_similar: bool = False
    create_backup: bool = True
    
    # Manual resolution details (if strategy is MANUAL_MERGE)
    manual_resolution: ManualResolutionData | None = None
```

### 4. Conflict Resolution Response

```python
@dataclass
class ConflictResolutionResponse:
    """Response from conflict resolution attempt."""
    
    success: bool
    resolution_id: UUID
    timestamp: datetime
    
    # Resolution details
    conflict_id: UUID
    applied_strategy: ConflictResolutionStrategy
    resolution_effectiveness: float  # 0.0 to 1.0
    
    # Result information
    resolved_note: ResolvedNote
    version_history_entry: VersionHistory
    backup_created: bool
    
    # Audit information
    resolution_metadata: dict[str, Any]
    user_intervention_required: bool
    follow_up_actions: list[FollowUpAction]
```

## Database Schema Extensions

### 1. Conflict Detection Results Table

```sql
CREATE TABLE conflict_detection_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES notes(id),
    analysis_timestamp TIMESTAMPTZ NOT NULL,
    conflict_type VARCHAR(20) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    
    -- Analysis results (JSONB for flexibility)
    content_analysis JSONB NOT NULL,
    metadata_analysis JSONB NOT NULL,
    structural_analysis JSONB NOT NULL,
    semantic_analysis JSONB,
    
    -- Resolution tracking
    resolved BOOLEAN DEFAULT FALSE,
    resolution_timestamp TIMESTAMPTZ,
    resolution_strategy VARCHAR(20),
    
    -- Performance metrics
    analysis_duration FLOAT,
    cache_used BOOLEAN,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conflict_detection_note_id ON conflict_detection_results(note_id);
CREATE INDEX idx_conflict_detection_timestamp ON conflict_detection_results(analysis_timestamp);
CREATE INDEX idx_conflict_detection_severity ON conflict_detection_results(severity);
```

### 2. Conflict Resolution Audit Table

```sql
CREATE TABLE conflict_resolution_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conflict_id UUID NOT NULL REFERENCES conflict_detection_results(id),
    resolution_timestamp TIMESTAMPTZ NOT NULL,
    
    -- Resolution details
    strategy_used VARCHAR(20) NOT NULL,
    user_id UUID REFERENCES users(id),
    automated_resolution BOOLEAN NOT NULL,
    
    -- Result tracking
    success BOOLEAN NOT NULL,
    effectiveness_score FLOAT,
    notes_created INT,
    notes_updated INT,
    notes_deleted INT,
    
    -- Backup information
    backup_created BOOLEAN,
    backup_location VARCHAR(255),
    
    -- Audit metadata
    resolution_metadata JSONB,
    error_details TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_resolution_audit_conflict ON conflict_resolution_audit(conflict_id);
CREATE INDEX idx_resolution_audit_timestamp ON conflict_resolution_audit(resolution_timestamp);
```

## Configuration Models

### 1. Conflict Detection Configuration

```python
@dataclass
class ConflictDetectionConfig:
    """Configuration for conflict detection behavior."""
    
    # Analysis settings
    enable_semantic_analysis: bool = True
    enable_structural_analysis: bool = True
    semantic_analysis_threshold: float = 0.8
    content_similarity_threshold: float = 0.9
    
    # Performance settings
    max_concurrent_analyses: int = 10
    cache_ttl_seconds: int = 3600
    batch_size: int = 100
    
    # Quality settings
    minimum_confidence: float = 0.7
    require_manual_review: bool = False
    manual_review_threshold: float = 0.3
    
    # Integration settings
    version_history_integration: bool = True
    audit_trail_enabled: bool = True
```

### 2. Resolution Strategy Configuration

```python
@dataclass
class ResolutionStrategyConfig:
    """Configuration for automatic resolution strategies."""
    
    # Strategy preferences
    default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.SEMANTIC_MERGE
    fallback_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MANUAL_MERGE
    
    # Thresholds for automatic resolution
    auto_resolve_low_severity: bool = True
    auto_resolve_medium_severity: bool = False
    auto_resolve_high_severity: bool = False
    auto_resolve_critical_severity: bool = False
    
    # Merge settings
    semantic_merge_confidence_threshold: float = 0.8
    preserve_original_structure: bool = True
    conflict_marker_style: str = "standard"
```

## Integration Points

### 1. Version History Integration

```python
@dataclass
class ConflictVersionHistory:
    """Extended version history for conflict resolution."""
    
    version_history: VersionHistory
    conflict_metadata: ConflictResolutionMetadata
    resolution_audit_trail: list[ResolutionStep]
    
@dataclass
class ConflictResolutionMetadata:
    """Metadata specific to conflict resolution versions."""
    
    conflict_id: UUID
    resolution_strategy: ConflictResolutionStrategy
    pre_resolution_state: NoteState
    post_resolution_state: NoteState
    conflict_hotspots_resolved: list[str]
    quality_improvements: list[QualityImprovement]
```

This data model provides a comprehensive foundation for implementing advanced conflict detection and resolution capabilities while maintaining constitutional compliance and performance standards.