# Tasks: AI Knowledge Base

**Input**: Design documents from `/specs/master/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - included based on constitutional requirement for test-first development (FR-016)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**⚠️ Vault-Sync Complexity Note**: Vault synchronization is included from the start due to existing Obsidian legacy data, but requires robust conflict detection, metadata mapping, and monitoring safeguards.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan in src/ and tests/
- [x] T002 Initialize Python 3.11+ project with dependencies in pyproject.toml
- [x] T003 [P] Configure linting and formatting tools with ruff and pytest in pyproject.toml
- [x] T004 [P] Setup PostgreSQL with PGVector extension configuration in config/database.env
- [x] T005 [P] Create Docker containerization setup in docker-compose.yml and Dockerfile

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Setup database schema and migrations framework in src/cli/migrate.py
- [x] T007 [P] Implement base Pydantic models for all entities in src/models/
- [x] T008 [P] Setup API routing and middleware structure in src/api/main.py
- [ ] T009 Configure error handling and logging infrastructure in src/utils/logging.py
- [x] T010 Setup environment configuration management in config/
- [x] T011 [P] Create base service layer interfaces in src/services/base.py
- [x] T012 Implement constitutional compliance framework in src/compliance/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Manual Note Creation & Management (Priority: P1) 🎯 MVP

**Goal**: Deliver complete note management system with CRUD operations, metadata, linking, and versioning

**Independent Test**: Create, read, update, delete notes with full metadata and version history tracking

### Tests for User Story 1 (Constitutional Requirement FR-016)

- [ ] T013 [P] [US1] Contract test for note CRUD operations in tests/contract/test_notes.py
- [ ] T014 [P] [US1] Integration test for manual note workflow in tests/integration/test_note_management.py
- [ ] T015 [P] [US1] Performance test for CRUD operations in tests/performance/test_note_performance.py

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create Note model with constitutional fields in src/models/note.py
- [ ] T017 [P] [US1] Create Link model for relationships in src/models/link.py
- [ ] T018 [P] [US1] Create VersionHistory model in src/models/version_history.py
- [ ] T019 [US1] Implement NoteService with CRUD operations in src/services/note_service.py
- [ ] T020 [US1] Implement LinkService for relationship management in src/services/link_service.py
- [ ] T021 [US1] Implement VersionService for audit trails in src/services/version_service.py
- [ ] T022 [US1] Implement note endpoints in src/api/notes.py
- [ ] T023 [US1] Add validation and error handling for constitutional compliance
- [ ] T024 [US1] Add logging for note operations with provenance tracking

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Semantic/Hybrid Search (Priority: P2)

**Goal**: Deliver hybrid search combining metadata filtering with semantic vector search

**Independent Test**: Search notes by metadata filters and semantic similarity with performance benchmarks

### Tests for User Story 2 (Constitutional Requirement FR-016)

- [ ] T025 [P] [US2] Contract test for search endpoints in tests/contract/test_search.py
- [ ] T026 [P] [US2] Integration test for hybrid search workflow in tests/integration/test_search.py
- [ ] T027 [P] [US2] Performance test for search operations in tests/performance/test_search_performance.py

### Implementation for User Story 2

- [ ] T028 [P] [US2] Create Embedding model for vector storage in src/models/embedding.py
- [ ] T029 [US2] Implement EmbeddingService for vector generation in src/services/embedding_service.py
- [ ] T030 [US2] Implement SearchService for hybrid search in src/services/search_service.py
- [ ] T031 [US2] Implement search endpoints in src/api/search.py
- [ ] T032 [US2] Add dual-index strategy for performance optimization
- [ ] T033 [US2] Integrate with User Story 1 components for note data access

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - External Content Ingestion (Priority: P3)

**Goal**: Deliver ingestion pipeline for PDF, web content, and text with constitutional data governance

**Independent Test**: Ingest external content with text extraction, embedding, and metadata preservation

### Tests for User Story 3 (Constitutional Requirement FR-016)

- [ ] T034 [P] [US3] Contract test for ingestion endpoints in tests/contract/test_ingestion.py
- [ ] T035 [P] [US3] Integration test for ingestion workflow in tests/integration/test_ingestion.py
- [ ] T036 [P] [US3] Performance test for ingestion operations in tests/performance/test_ingestion_performance.py

### Implementation for User Story 3

- [ ] T037 [P] [US3] Create IngestionService for content processing in src/services/ingestion/ingestion_service.py
- [ ] T038 [P] [US3] Implement PDF parser in src/services/ingestion/pdf_parser.py
- [ ] T039 [P] [US3] Implement web content parser in src/services/ingestion/web_parser.py
- [ ] T040 [US3] Implement text processing pipeline in src/services/ingestion/text_processor.py
- [ ] T041 [US3] Implement ingestion endpoints in src/api/ingestion.py
- [ ] T042 [US3] Add error handling and retry logic for constitutional compliance
- [ ] T043 [US3] Integrate with User Stories 1 and 2 for note creation and embedding

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Agent Workflow Integration (Priority: P4)

**Goal**: Deliver AI agent framework with constitutional compliance (audit trails, human review)

**Independent Test**: Execute agent workflows with audit logging and human review gates

### Tests for User Story 4 (Constitutional Requirement FR-016)

- [ ] T044 [P] [US4] Contract test for agent interfaces in tests/contract/test_agents.py
- [ ] T045 [P] [US4] Integration test for agent workflows in tests/integration/test_agent_workflows.py
- [ ] T046 [P] [US4] Performance test for agent operations in tests/performance/test_agent_performance.py

### Implementation for User Story 4

- [ ] T047 [P] [US4] Create AgentRun model for audit trails in src/models/agent_run.py
- [ ] T048 [US4] Implement AgentService with PydanticAI integration in src/services/agents/agent_service.py
- [ ] T049 [US4] Implement research agent workflow in src/services/agents/research_agent.py
- [ ] T050 [US4] Implement human review workflow in src/services/agents/review_service.py
- [ ] T051 [US4] Implement agent endpoints in src/api/agent.py
- [ ] T052 [US4] Add SpiffWorkflow orchestration in src/workflows/
- [ ] T053 [US4] Integrate with all previous user stories for full knowledge base access

**Checkpoint**: AI agent workflows should work with constitutional compliance

---

## Phase 7: User Story 5 - Vault Synchronization (Priority: P5)

**Goal**: Deliver optional Obsidian vault synchronization with conflict resolution

**Independent Test**: Bidirectional sync between database and markdown vault with conflict detection

### Tests for User Story 5 (Constitutional Requirement FR-016)

- [ ] T054 [P] [US5] Contract test for vault sync interfaces in tests/contract/test_vault.py
- [ ] T055 [P] [US5] Integration test for sync workflows in tests/integration/test_vault_sync.py
- [ ] T056 [P] [US5] Performance test for sync operations in tests/performance/test_vault_performance.py
- [ ] T057 [P] [US5] Conflict detection and resolution tests in tests/integration/test_vault_conflicts.py
- [ ] T058 [P] [US5] Metadata mapping validation tests in tests/unit/test_vault_metadata.py
- [ ] T059 [P] [US5] Backup and recovery tests for sync operations in tests/integration/test_vault_backup.py

### Implementation for User Story 5

- [ ] T060 [P] [US5] Research and setup Obsidian Local REST API integration in src/services/vault/obsidian_api.py
- [ ] T061 [P] [US5] Define metadata mapping schema between DB and front-matter in src/services/vault/metadata_schema.py
- [ ] T062 [US5] Implement VaultService with bidirectional sync protocol in src/services/vault/vault_service.py
- [ ] T063 [US5] Implement robust conflict detection with timestamp/version tracking in src/services/vault/conflict_detector.py
- [ ] T064 [US5] Implement manual conflict resolution workflow in src/services/vault/conflict_resolver.py
- [ ] T065 [US5] Implement embedding/index update triggers on vault changes in src/services/vault/embedding_sync.py
- [ ] T066 [US5] Implement backup and version control for sync operations in src/services/vault/backup_manager.py
- [ ] T067 [US5] Implement comprehensive sync monitoring and audit logging in src/services/vault/sync_monitor.py
- [ ] T068 [US5] Implement vault endpoints with sync status reporting in src/api/vault.py
- [ ] T069 [US5] Add Obsidian MCP server integration in src/mcp/obsidian_server.py
- [ ] T070 [US5] Create user documentation for vault sync workflow in docs/vault-sync-guide.md

**Checkpoint**: Vault sync should work as optional progressive enhancement

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T071 [P] Documentation updates in docs/ with constitutional compliance guides
- [ ] T072 [P] Code cleanup and refactoring across all services
- [ ] T073 Performance optimization across all stories with benchmarking
- [ ] T074 [P] Additional unit tests in tests/unit/ for comprehensive coverage
- [ ] T075 Security hardening with constitutional audit requirements
- [ ] T076 Run quickstart.md validation and update based on implementation
- [ ] T077 [P] Create MCP server implementations in src/mcp/ for external tool integration
- [ ] T078 Implement monitoring and alerting for constitutional compliance metrics
- [ ] T079 Setup backup and recovery procedures with rollback testing
- [ ] T080 [P] Create vault sync monitoring dashboard in src/monitoring/vault_sync_dashboard.py
- [ ] T081 Implement sync health checks and alerting in src/monitoring/sync_health.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for note data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1, US2, US3
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - Depends on all previous stories
  - **⚠️ Vault-Sync Complexity**: Requires robust conflict detection, metadata mapping, and monitoring
  - **Safety Measures**: Backup/versioning, manual conflict resolution, embedding sync triggers

### Within Each User Story

- Tests (constitutional requirement) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories can start in parallel (with dependency awareness)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for note CRUD operations in tests/contract/test_notes.py"
Task: "Integration test for manual note workflow in tests/integration/test_note_management.py"
Task: "Performance test for CRUD operations in tests/performance/test_note_performance.py"

# Launch all models for User Story 1 together:
Task: "Create Note model with constitutional fields in src/models/note.py"
Task: "Create Link model for relationships in src/models/link.py"
Task: "Create VersionHistory model in src/models/version_history.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core note management)
   - Developer B: User Story 2 (Search) - starts after US1 models
   - Developer C: User Story 3 (Ingestion) - starts after US1 and US2
   - Developer D: User Story 4 (Agents) - starts after US1-3
   - Developer E: User Story 5 (Vault) - starts after US1-4
3. Stories complete and integrate with dependency management

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (constitutional requirement)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitutional compliance must be verified at each phase
- Performance benchmarks must be maintained throughout development
- **Vault-Sync Safety**: Always backup before sync, monitor conflicts, limit to text-only initially
- **Conflict Management**: Manual review required for all sync conflicts, no silent auto-merges
- **Metadata Consistency**: Clear ownership rules for DB-managed vs user-editable metadata fields