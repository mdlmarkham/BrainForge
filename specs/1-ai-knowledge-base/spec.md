# BrainForge — Software Requirements Specification (SRS) v1.1

## Revision History

| Version | Date       | Author | Notes |
|--------:|------------|--------|---------------------------|
| 1.1     | 2025-11-28 | You    | Constitution alignment - added AI governance, test-first development, human-in-the-loop requirements |
| 1.0     | 2025-11-28 | You    | Initial full SRS draft    |

---

## Table of Contents

1. [Introduction](#1-introduction)  
   1. [Purpose](#11-purpose-of-this-document)  
   2. [Intended Audience & Stakeholders](#12-intended-audience--stakeholders)  
   3. [Scope of the Product](#13-scope-of-the-product)  
   4. [Definitions, Acronyms & Abbreviations](#14-definitions-acronyms--abbreviations)  
2. [Overall Description](#2-overall-description)  
   1. [Product Perspective](#21-product-perspective)  
   2. [User Classes & Characteristics](#22-user-classes--characteristics)  
   3. [Constraints, Assumptions, Dependencies](#23-constraints-assumptions-dependencies)  
3. [System Features & Requirements](#3-system-features--requirements)  
   1. [Functional Requirements](#31-functional-requirements)  
   2. [Non-Functional Requirements (Quality Attributes)](#32-non-functional-requirements-quality-attributes)  
   3. [External Interface Requirements](#33-external-interface-requirements)  
4. [Use Cases / Primary Scenarios](#4-use-cases--primary-scenarios)  
   1. [Manual Note Creation & Management](#41-use-case-manual-note-creation--management)  
   2. [External Content Ingestion (PDF / Web)](#42-use-case-external-content-ingestion-pdf--web)  
   3. [Semantic / Hybrid Search](#43-use-case-semantic--hybrid-search)  
   4. [Agent Workflow — Research / Insight Generation](#44-use-case-agent-workflow--research--insight-generation)  
   5. [Vault Sync (Export / Import)](#45-use-case-vault-sync-export--import)  
5. [System Architecture Overview (Sketch)](#5-system-architecture-overview-sketch)  
6. [Constraints, Assumptions & Dependencies](#6-constraints-assumptions--dependencies)  
7. [Risks, Failure Modes & Mitigations](#7-risks-failure-modes--mitigations)  
8. [Future Extensions (Beyond v1.0)](#8-future-extensions-beyond-v10)  
9. [Constitution Compliance](#9-constitution-compliance)
10. [Appendix — Glossary of Key Terms](#10-appendix--glossary-of-key-terms)

---

## 1. Introduction

### 1.1 Purpose of this Document  
This document defines the functional and non-functional requirements for BrainForge — an AI-powered personal knowledge management and thinking environment. It serves as a single source of truth for developers, testers, and future maintainers, specifying what the system must do, and the constraints under which it should operate.

### 1.2 Intended Audience & Stakeholders  
- **Primary user / owner** — the person building and using BrainForge.  
- **Developers / engineers** — those who implement and maintain the system.  
- **Testers / QA** — responsible for validating the behavior against requirements.  
- **Future collaborators / contributors** — who may extend the system with new features.  

### 1.3 Scope of the Product  
BrainForge is a personal knowledge system combining:  
- Human-friendly note creation/editing and organization (tags, metadata, linking).  
- Ingestion of external content (PDFs, web pages, text) into structured “literature” notes, with metadata and semantic embeddings.  
- Semantic and metadata-based search (including hybrid search).  
- Explicit relational link-graph between notes for structured idea networks.  
- AI-agent integration (research, analysis, fact-checking) that can read/write notes programmatically.  
- Auditability: provenance, versioning, agent-run logging.  
- Optional synchronization with a markdown vault / human-readable note layer for manual editing / browsing.  

### 1.4 Definitions, Acronyms & Abbreviations  

| Term / Acronym     | Definition |
|--------------------|------------|
| **Note**           | A core unit of knowledge (fleeting, literature, permanent, insight, or agent-generated). |
| **Metadata**       | Attributes associated with a Note: ID, timestamps, tags, type, provenance, version history, etc. |
| **Embedding**      | A vector representation of Note content used for semantic similarity search. |
| **Link / Relationship** | An explicit connection between two Notes, annotated with a “relation type” (e.g. `cites`, `supports`, `derived_from`, `related`). |
| **Vault**          | Optional human-readable markdown-based representation of the knowledge base for manual editing / reading. |
| **Agent**          | Automated AI components (researcher, analyzer, fact-checker) able to read/write Notes. |
| **AgentRun**       | Logged execution record of an Agent’s action: inputs, outputs, timestamps, status, errors. |
| **Hybrid Search**  | Search combining metadata filters (tags, type, links) with embedding-based semantic similarity. |

---

## 2. Overall Description

### 2.1 Product Perspective  
BrainForge is a self-contained, personal knowledge system. The canonical data store is a relational database (e.g. PostgreSQL + vector extension) that supports structured metadata, embeddings, and relational links. A markdown-based vault or human-facing UI layer — if used — serves as a secondary interface for manual editing and browsing. Agents, ingestion pipelines, and vector search operate against the database.

### 2.2 User Classes & Characteristics  

| User Class         | Description                              | Permissions / Responsibilities |
|--------------------|------------------------------------------|-------------------------------|
| Owner (Primary User) | Single-person user managing their PKB   | Create, edit, finalize, delete notes; ingest content; review and approve agent output; manage metadata and links; oversee all operations. |
| Developer / Maintainer | Person(s) building/maintaining system         | Develop and maintain ingestion, embedding, APIs, DB schema, backups, etc. |
| Agent (Automated)  | AI agents interacting via API            | Read/write notes, create new knowledge items, link notes, embed content, log provenance. Agent outputs require human review before finalization. |
| Reviewer           | Human reviewer for AI-generated content | Review, validate, and approve agent-generated content; ensure accuracy, relevance, and timeliness; prune outdated information. |
| Tester / QA        | Verifiers of functionality, performance   | Validate features, execute test cases, perform quality/performance tests, backup/recovery tests. |

### 2.3 Constraints, Assumptions & Dependencies  
- Initial deployment is local or on a private server; not a cloud multi-tenant system.  
- Default usage is by a single user (no multi-user access control).  
- Content is primarily text (markdown, plain text, extracted text from PDFs or web pages). Media types beyond text (images, audio, video) may be considered in future versions.  
- Embedding model must be selected (locally hosted or external); embedding dimension remains fixed for compatibility.  
- Vault sync (if used) is optional — canonical storage remains the database.  
- External libraries for parsing PDFs / HTML / web scraping required for ingestion; system must handle parsing failures gracefully.

---

## 3. System Features & Requirements

### 3.1 Functional Requirements  

| ID     | Requirement                                                                 |
|--------|------------------------------------------------------------------------------|
| FR-001 | The system shall allow creation, reading, updating, and deletion (CRUD) of Notes (all types). |
| FR-002 | Each Note shall store metadata including unique ID, timestamps (created/modified), note type, tags, provenance, version history, and explicit distinction between AI-generated and human-authored content. |
| FR-003 | The system shall support explicit relationships (links) between Notes, with defined relation types (e.g. `cites`, `supports`, `derived_from`, `related`). |
| FR-004 | For each Note (or note chunk), the system shall compute and store an embedding vector in the semantic index. |
| FR-005 | The system shall support ingestion of external content (PDF, web page, plain text, markdown), including text extraction, optional chunking, embedding, and storing as "literature" Notes with metadata, provenance, source metadata, license information, and format validation. |
| FR-006 | The system shall support search/filtering by metadata (tags, note type, dates, links). |
| FR-007 | The system shall support semantic search: given a textual or embedding query, return nearest-neighbor notes via vector similarity search. |
| FR-008 | The system shall support hybrid search combining metadata filters with semantic similarity. |
| FR-009 | The system shall expose a well-defined API for Agents (or tools) to read and write Notes, metadata, relationships, and embeddings. The API shall include appropriate authentication/authorization, provenance metadata, and complete audit trails. |
| FR-010 | The system shall log each AgentRun with details: agent identity, version, input parameters, output note IDs, timestamps, status (success/fail), errors if any, and human review gates for critical operations. |
| FR-011 | The system shall maintain version history of Notes (content, metadata, links); previous versions must be preserved and retrievable; changes must be reversible (rollback); and conflict resolution mechanisms must handle AI-human collaboration scenarios. |
| FR-012 | (Optional) The system shall support synchronization between the canonical store and a markdown-based vault: export notes to markdown (front-matter metadata + body + links), and import changes from vault back to canonical store. |
| FR-013 | When vault-sync is enabled, the system shall detect sync conflicts (e.g. simultaneous edits in DB and vault) and provide a conflict-resolution mechanism (merge prompts, manual review, alert). |
| FR-014 | The system shall support workflow orchestration: ingestion → embedding → storage; Agent workflows (research / analysis / fact-check); embedding re-index on note edits; with ability to schedule or manually trigger runs. |
| FR-015 | The system shall support auditability & traceability: note provenance, version history, link graph evolution, and AgentRun logs must be preserved for review. |
| FR-016 | The system shall implement comprehensive test coverage for critical data operations before AI integration, including contract testing for AI agent interfaces and performance benchmarks for AI-enhanced workflows. |
| FR-017 | Core functionality shall work without AI dependencies, with AI features being additive and optional. Simple workflows must remain accessible without requiring AI capabilities. |
| FR-018 | The system shall define clear user roles (Owner, Agent, Reviewer) with associated permissions (create, edit, finalize, delete, review). Agent outputs marked as "final" must pass human review and approval before integration into the canonical knowledge base. |
| FR-019 | All operations (ingestion, embedding, agent-writing, sync) shall implement error detection, retry logic, comprehensive logging, and support periodic backups with restore/rollback tools. |
| FR-020 | Each deployed agent shall carry a version identifier with changes tracked in version control. New agent versions must pass behavior verification tests before deployment. |
| FR-021 | AI-generated content shall include justification/rationale in structured metadata and undergo regular human review cycles for accuracy, relevance, and timeliness validation. |

### 3.2 Non-Functional Requirements (Quality Attributes)  

| ID      | Requirement / Target |
|---------|----------------------|
| NFR-001 | Basic CRUD and metadata search shall complete within ~1 second for databases up to 10,000 notes. |
| NFR-002 | Ingestion + embedding of a standard document (≤ 50 pages) shall complete within ~2 minutes (on baseline hardware). |
| NFR-003 | Semantic or hybrid search over ~10,000 notes shall return top-10 results within ~500 ms (excluding embedding generation). |
| NFR-004 | The system design shall allow scaling to larger datasets (e.g. 100k+ notes) via indexing, sharding, caching, or other scaling strategies. |
| NFR-005 | The system must preserve data integrity under crashes or shutdowns; support transactional updates, backups, and restore functionality. |
| NFR-006 | The data model (schema, metadata, link types, embedding settings) shall be designed for extensibility — supporting new note types, metadata fields, embedding models, link types, without breaking backward compatibility. |
| NFR-007 | If a vault (markdown) view is used, exported markdown must remain human-readable, preserve internal links and metadata, and be easily editable without losing structure. |
| NFR-008 | (If sensitive content is stored) Data at rest and in transit must be appropriately protected (encryption, access control, secure handling of external content). |
| NFR-009 | System logs (ingestion, agent runs, syncs, search) shall be maintained; system shall provide observability and debuggability (logging, audit trails, error reporting). |

### 3.3 External Interface Requirements  

The system must define interfaces including:  
- **Agent Interface / API** — for agents/tools to read/write notes, metadata, perform search, submit ingestion tasks, retrieve logs.  
- **Vault Synchronization Interface** — export/import between canonical store and markdown vault; mapping metadata ↔ front-matter; link syntax ↔ relational links; conflict detection/resolution.  
- **Ingestion Interface** — import external content (PDF, HTML, markdown, plain text), with parameters for source, parsing method, chunking policy, metadata.  
- **Embedding Interface** — integration point for embedding model/service: input text → output vector; handle failures, versioning, re-embedding on updates.  

---

## 4. Use Cases / Primary Scenarios

### 4.1 Use Case: Manual Note Creation & Management  
**Actor:** Primary User  
**Flow:** Create → edit → delete notes; assign tags/metadata; optionally produce version history; retrieve notes via search or browsing.  

### 4.2 Use Case: External Content Ingestion (PDF / Web Page)  
**Actor:** User or Agent  
**Flow:** Upload or supply URL → system extracts text → chunk (if needed) → compute embedding → store as literature Notes with metadata & provenance → index for search.  

### 4.3 Use Case: Semantic / Hybrid Search  
**Actor:** User or Agent  
**Flow:** Provide text or embedding query + optional metadata filters → system returns ranked list of relevant notes with similarity scores and metadata.  

### 4.4 Use Case: Agent Workflow — Research / Insight Generation  
**Actor:** AI Agent via API  
**Flow:** Agent retrieves existing notes (search) → performs analysis/synthesis → generates new Notes (insights/composite) → system persists notes, embeddings, links; logs AgentRun.  

### 4.5 Use Case: Vault Sync (Export / Import)  
**Actor:** User or automated sync process  
**Flow — Export:** DB → markdown vault; **Import:** vault → DB; with conflict detection & resolution if both sides changed.  

---

## 5. System Architecture Overview (Sketch)

- **Storage Layer:** Relational database (e.g. PostgreSQL) with vector extension for embeddings & semantic index.  
- **Data Model:** Tables for Notes, Embeddings, Metadata, Links (relationships), AgentRuns (logs), Version history.  
- **Ingestion Layer:** Pipelines to parse PDFs / HTML / text / markdown, chunk, embed, store.  
- **Search Layer:** Semantic search (vector queries), metadata filter search, hybrid search API.  
- **Agent Interface / API Layer:** For automated agents to read/write, link notes, trigger workflows, log runs.  
- **Vault Sync Layer (optional):** Export/import logic for markdown vault; conflict detection / resolution.  
- **Workflow Orchestration:** Engines or scripts to manage ingestion → embedding → storage processes; agent workflows; periodic maintenance tasks.  
- **Logging / Audit / Versioning:** For all operations (user or agent), with provenance, history, and rollback support.  

---

## 6. Constraints, Assumptions & Dependencies

- Embedding model must exist and remain compatible (fixed dimension, stable API).  
- System deployed for single-user use initially (not multi-user, not public).  
- Content is primarily text; non-text media support is not in v1.0.  
- Vault sync is optional; canonical store remains database.  
- External dependencies: PDF parse libraries, HTML scraper / web-fetch libraries for ingestion; potential external APIs or local models for embedding.  
- Performance expectations are approximate and may vary depending on hardware, load, and note volume.  

---

## 7. Risks, Failure Modes & Mitigations

| Risk / Failure Mode | Impact | Mitigation |
|---------------------|--------|-------------|
| Parsing / ingestion failures (e.g. bad PDF, malformed HTML) | Partial or failed ingestion → lost content or errors | Validate inputs, handle errors gracefully, log failures, skip or retry imports. |
| Embedding failures / model unavailability | Semantic search unavailable, embeddings missing | Fallback to metadata-only search; queue embeddings for retry; alert user. |
| Vault-DB sync conflicts | Data inconsistency, lost edits, corruption | Use versioning, conflict detection, manual merge or review steps, lock during sync. |
| Scale / performance degradation with large note base | Slow search, lag, poor UX | Use indexing, caching, vector index optimizations, sharding or partitioning if needed. |
| Data corruption or accidental deletion | Loss of user knowledge base | Use transactions, backups, version history, provide restore mechanism. |
| Agent-generated incorrect or low-quality content | Polluted knowledge base, loss of trust | Record provenance, require human review for agent output, support note deprecation or revision. |

---

## 8. Future Extensions (Beyond v1.0)

Potential enhancements:  
- Support for rich media (images, tables, audio, video) in notes.  
- Multi-user / collaboration features, permissions, roles.  
- Web or desktop UI / front-end with interactive note editing, graph visualization, dashboards, review workflows.  
- Advanced knowledge-graph / ontology capabilities (entity extraction, semantic relations, inference, taxonomy).  
- Scheduled maintenance tasks: periodic re-embedding, fact-checking, content re-validation, pruning obsolete notes.  
- Export/import to additional formats; integration with other PKM tools or external data sources.  

---

## 9. Constitution Compliance

This specification has been designed to comply with the BrainForge Constitution v1.1.0. The following table demonstrates alignment with each constitutional principle:

| Constitutional Principle | Specification Compliance | Relevant Requirements |
|--------------------------|--------------------------|----------------------|
| **I. Structured Data Foundation** | ✅ FULLY COMPLIANT | FR-002, FR-003, FR-011, NFR-006 |
| **II. AI Agent Integration** | ✅ FULLY COMPLIANT | FR-009, FR-010, FR-020 |
| **III. Versioning & Auditability** | ✅ FULLY COMPLIANT | FR-002, FR-011, FR-015 |
| **IV. Test-First Development** | ✅ FULLY COMPLIANT | FR-016 |
| **V. Progressive Enhancement** | ✅ FULLY COMPLIANT | FR-017 |
| **VI. Roles, Permissions, and Ownership** | ✅ FULLY COMPLIANT | Section 2.2, FR-018 |
| **VII. Data Governance & External Content Policy** | ✅ FULLY COMPLIANT | FR-005, FR-019 |
| **VIII. Error Handling & Recovery Policy** | ✅ FULLY COMPLIANT | FR-019, Section 7 |
| **IX. AI Agent Versioning & Governance** | ✅ FULLY COMPLIANT | FR-010, FR-020 |
| **X. Human-in-the-Loop & Explainability Standard** | ✅ FULLY COMPLIANT | FR-002, FR-018, FR-021 |

### Compliance Verification Process

All feature implementations MUST verify compliance with these constitutional principles through:

1. **Architectural Review**: Data schema changes and AI agent integrations require review against constitutional principles
2. **Security Review**: AI agent integrations and external content processing require security and auditability review
3. **Performance Validation**: Performance-impacting changes require benchmark validation
4. **Backward Compatibility**: All changes must maintain backward compatibility for existing data

### Development Workflow Alignment

This specification aligns with the constitutional development workflow:

1. **Data Model First**: Clear data structures defined before AI integration (Sections 1.4, 2.1, 5)
2. **Human Workflow Validation**: Manual operations work reliably (Use Cases 4.1, 4.2, 4.5)
3. **AI Enhancement**: AI capabilities added as optional extensions (FR-017, Use Case 4.4)
4. **Integration Testing**: AI-human collaboration scenarios validated (FR-016, FR-021)

## 10. Appendix — Glossary of Key Terms

See Definitions in Section 1.4. Additional terms may be added as the project evolves.

---

