# Implementation Plan: PDF Processing for Ingestion Curation

**Branch**: `002-ingestion-curation` | **Date**: 2025-11-29 | **Spec**: `/specs/002-ingestion-curation/spec.md`
**Input**: Feature specification from `/specs/002-ingestion-curation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add PDF processing capability to the ingestion curation pipeline using dockling for text extraction, enabling automated ingestion of PDF documents with summarization, classification, and integration into the knowledge graph.

## Technical Context

**Language/Version**: Python 3.11+ (constitution requirement)
**Primary Dependencies**: FastAPI, PostgreSQL/PGVector, PydanticAI, SQLAlchemy, dockling (PDF processing)
**Storage**: PostgreSQL with PGVector extension for semantic indexing
**Testing**: pytest with contract testing for PDF processing interfaces
**Target Platform**: Linux server (containerized deployment)
**Project Type**: single project (API service)
**Performance Goals**: Process PDF documents within 2 minutes for typical academic papers (20-30 pages)
**Constraints**: Maintain backward compatibility with existing ingestion pipeline, support PDFs up to 100MB
**Scale/Scope**: Handle dozens of PDFs per month for personal knowledge management use cases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Structured Data Foundation**: ✅ PDF processing will extend existing ingestion data models with PDF-specific metadata
**AI Agent Integration**: ✅ PDF processing will use dockling with clear input/output contracts and audit trails
**Versioning & Auditability**: ✅ PDF ingestion will maintain complete version history and rollback capabilities
**Test-First Development**: ✅ PDF processing will have comprehensive test coverage before integration
**Progressive Enhancement**: ✅ PDF processing will be optional enhancement to existing ingestion pipeline
**Roles & Permissions**: ✅ PDF ingestion will follow existing user/agent roles and approval workflows
**Data Governance**: ✅ PDF processing will include source validation and license compliance checks
**Error Handling**: ✅ PDF processing will implement retry logic and graceful failure handling
**AI Versioning**: ✅ dockling integration will use versioned interfaces with behavior verification
**Human-in-the-Loop**: ✅ PDF processing results will require human review before final integration

*All constitutional gates passed - feature design is compliant*

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/                          # Existing data models
│   ├── ingestion.py                 # NEW: PDF ingestion models
│   └── pdf_metadata.py              # NEW: PDF-specific metadata
├── services/
│   ├── pdf_processor.py             # NEW: PDF processing service with dockling
│   └── ingestion.py                 # Extend existing ingestion service
├── api/routes/
│   └── ingestion.py                 # Extend existing ingestion routes
└── cli/
    └── pdf_ingest.py                # NEW: CLI for PDF ingestion

tests/
├── contract/
│   └── test_pdf_processing.py       # NEW: PDF processing contract tests
├── integration/
│   └── test_pdf_ingestion.py        # NEW: PDF ingestion integration tests
└── unit/
    └── test_pdf_processor.py        # NEW: PDF processor unit tests
```

**Structure Decision**: Single project structure selected as this extends existing ingestion pipeline. New PDF-specific modules will be added to existing directories while maintaining separation of concerns.

## Phase 0: Research Complete

**Status**: All research tasks completed and documented in `research.md`

**Key Decisions**:
- Use dockling for PDF text extraction and metadata collection
- Extend existing ingestion architecture with PDF-specific services
- Maintain backward compatibility with current ingestion pipeline
- Implement comprehensive error handling and retry logic

## Phase 1: Design Complete

**Status**: Design artifacts generated and ready for implementation

**Generated Artifacts**:
- `data-model.md`: Extended data models for PDF processing
- `contracts/openapi.yaml`: API specifications for PDF ingestion endpoints
- `quickstart.md`: Implementation guide with code examples

**Constitution Check Re-evaluation**:

**Structured Data Foundation**: ✅ PDFMetadata model extends existing ingestion data structure
**AI Agent Integration**: ✅ dockling integration with clear contracts and audit trails
**Versioning & Auditability**: ✅ Complete version history for PDF processing activities
**Test-First Development**: ✅ Comprehensive test plan included in quickstart
**Progressive Enhancement**: ✅ PDF processing optional enhancement to existing pipeline
**Roles & Permissions**: ✅ Follows existing user/agent role definitions
**Data Governance**: ✅ PDF validation and security checks implemented
**Error Handling**: ✅ Retry logic and graceful failure handling designed
**AI Versioning**: ✅ dockling version tracking included
**Human-in-the-Loop**: ✅ Review workflow maintained for PDF content

*All constitutional requirements maintained - design approved*

## Next Steps

Proceed to implementation phase using the generated artifacts:
1. Implement data models from `data-model.md`
2. Build services following `quickstart.md` examples
3. Implement API endpoints from `contracts/openapi.yaml`
4. Run comprehensive testing before deployment

**Branch**: `002-ingestion-curation`
**IMPL_PLAN Path**: `specs/master/plan.md`
**Generated Artifacts**: `research.md`, `data-model.md`, `contracts/openapi.yaml`, `quickstart.md`
