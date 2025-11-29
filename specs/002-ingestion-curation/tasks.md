# Tasks: Ingestion and Curation Pipeline

**Input**: Design documents from `/specs/master/` and `/specs/002-ingestion-curation/spec.md`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - included based on constitutional requirement for test-first development (FR-016)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

## Phase 3: User Story 1 - Basic Content Ingestion (Priority: P1) 🎯 MVP

**Goal**: Deliver ingestion pipeline for web articles, videos, and text clips with constitutional data governance

**Independent Test**: Ingest external content with text extraction, embedding, and metadata preservation

### Tests for User Story 1 (Constitutional Requirement FR-016)

- [ ] T013 [P] [US1] Contract test for ingestion endpoints in tests/contract/test_ingestion.py
- [ ] T014 [P] [US1] Integration test for ingestion workflow in tests/integration/test_ingestion.py
- [ ] T015 [P] [US1] Performance test for ingestion operations in tests/performance/test_ingestion_performance.py

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create IngestionTask model with constitutional fields in src/models/ingestion.py
- [ ] T017 [P] [US1] Create ContentSource model for external content in src/models/content_source.py
- [ ] T018 [P] [US1] Create ProcessingResult model in src/models/processing_result.py
- [ ] T019 [US1] Implement IngestionService with content processing in src/services/ingestion/ingestion_service.py
- [ ] T020 [US1] Implement web content parser in src/services/ingestion/web_parser.py
- [ ] T021 [US1] Implement text processing pipeline in src/services/ingestion/text_processor.py
- [ ] T022 [US1] Implement ingestion endpoints in src/api/routes/ingestion.py
- [ ] T023 [US1] Add error handling and retry logic for constitutional compliance
- [ ] T024 [US1] Integrate with existing note management and embedding services

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Curation and Contextual Integration (Priority: P2)

**Goal**: Deliver automated content curation with semantic similarity analysis and connection suggestions

**Independent Test**: Ingest content related to existing notes and verify automatic connection suggestions

### Tests for User Story 2 (Constitutional Requirement FR-016)

- [ ] T025 [P] [US2] Contract test for curation endpoints in tests/contract/test_curation.py
- [ ] T026 [P] [US2] Integration test for curation workflow in tests/integration/test_curation.py
- [ ] T027 [P] [US2] Performance test for curation operations in tests/performance/test_curation_performance.py

### Implementation for User Story 2

- [ ] T028 [P] [US2] Create ReviewQueue model for human review in src/models/review_queue.py
- [ ] T029 [US2] Implement CurationService with semantic analysis in src/services/curation/curation_service.py
- [ ] T030 [US2] Implement connection suggestion engine in src/services/curation/connection_suggester.py
- [ ] T031 [US2] Implement classification service in src/services/curation/classification_service.py
- [ ] T032 [US2] Implement curation endpoints in src/api/routes/curation.py
- [ ] T033 [US2] Add semantic similarity analysis using existing embedding services
- [ ] T034 [US2] Integrate with User Story 1 components for processed content

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Human Review and Approval Workflow (Priority: P3)

**Goal**: Deliver human review interface for quality control with complete audit trails

**Independent Test**: Create review queue and verify human approval workflow with audit logging

### Tests for User Story 3 (Constitutional Requirement FR-016)

- [ ] T035 [P] [US3] Contract test for review endpoints in tests/contract/test_review.py
- [ ] T036 [P] [US3] Integration test for review workflow in tests/integration/test_review.py
- [ ] T037 [P] [US3] Performance test for review operations in tests/performance/test_review_performance.py

### Implementation for User Story 3

- [ ] T038 [P] [US3] Create AuditTrail model for provenance tracking in src/models/audit_trail.py
- [ ] T039 [US3] Implement ReviewService with approval workflow in src/services/review/review_service.py
- [ ] T040 [US3] Implement audit logging service in src/services/review/audit_service.py
- [ ] T041 [US3] Implement review endpoints in src/api/routes/review.py
- [ ] T042 [US3] Add human review interface with approval/rejection capabilities
- [ ] T043 [US3] Integrate with User Stories 1 and 2 for processed content and suggestions

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: PDF Processing Enhancement (Priority: P1.5)

**Goal**: Add PDF processing capability using dockling for text extraction

**Independent Test**: Process PDF documents with text extraction, summarization, and classification

### Tests for PDF Processing (Constitutional Requirement FR-016)

- [ ] T044 [P] [PDF] Contract test for PDF processing endpoints in tests/contract/test_pdf_processing.py
- [ ] T045 [P] [PDF] Integration test for PDF ingestion workflow in tests/integration/test_pdf_ingestion.py
- [ ] T046 [P] [PDF] Performance test for PDF operations in tests/performance/test_pdf_performance.py

### Implementation for PDF Processing

- [ ] T047 [P] [PDF] Create PDFMetadata model for PDF-specific metadata in src/models/pdf_metadata.py
- [ ] T048 [P] [PDF] Create PDFProcessingResult model in src/models/pdf_processing_result.py
- [ ] T049 [PDF] Implement PDFProcessor service with dockling integration in src/services/ingestion/pdf_processor.py
- [ ] T050 [PDF] Extend IngestionService to support PDF processing in src/services/ingestion/ingestion_service.py
- [ ] T051 [PDF] Add PDF-specific endpoints to ingestion routes in src/api/routes/ingestion.py
- [ ] T052 [PDF] Create database migration for PDF metadata tables in alembic/versions/002_add_pdf_processing.py
- [ ] T053 [PDF] Add PDF validation and error handling for constitutional compliance

**Checkpoint**: PDF processing should work as optional enhancement to existing ingestion pipeline

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T054 [P] Documentation updates in docs/ with constitutional compliance guides
- [ ] T055 [P] Code cleanup and refactoring across all services
- [ ] T056 Performance optimization across all stories with benchmarking
- [ ] T057 [P] Additional unit tests in tests/unit/ for comprehensive coverage
- [ ] T058 Security hardening with constitutional audit requirements
- [ ] T059 Run quickstart.md validation and update based on implementation
- [ ] T060 Implement monitoring and alerting for constitutional compliance metrics
- [ ] T061 Setup backup and recovery procedures with rollback testing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for processed content
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2
- **PDF Processing (P1.5)**: Can start after Foundational (Phase 2) - Integrates with US1

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

---

## Implementation Strategy

### MVP First (User Story 1 + PDF Processing)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic Content Ingestion)
4. Complete Phase 6: PDF Processing Enhancement
5. **STOP and VALIDATE**: Test ingestion pipeline independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add PDF Processing → Test independently → Deploy/Demo
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- PDF processing is prioritized as P1.5 due to high value and existing design artifacts