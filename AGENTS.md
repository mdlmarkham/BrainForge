# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Build/Test/Lint Commands

**Essential Commands:**
```bash
pytest tests/unit/test_specific.py    # Run single test
pytest tests/unit/                     # Run unit tests
pytest tests/integration/              # Run integration tests
pytest tests/                          # Run all tests
ruff check src/                        # Lint code
ruff format src/                       # Format code
black src/                             # Format fallback
mypy src/                              # Type checking
pytest --cov=src --cov-fail-under=80   # Coverage check
```

**Quality Gates (run before commit):**
```bash
pytest tests/unit/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=80
```

## Code Style Guidelines

**Python 3.11+** with strict typing and modern practices.

**Imports:** Use absolute imports from project root (`from src.models.orm.base import BaseEntity`)

**Formatting/Style:** Black 88 chars, Ruff for linting. Use type hints everywhere.

**Naming:** 
- Classes: PascalCase (`UserService`)
- Functions/variables: snake_case (`get_user_by_id`)
- Constants: UPPER_CASE (`MAX_RETRIES`)
- Private: underscore prefix (`_internal_method`)

**Type Annotations:** Use modern union syntax (`str | None`) and explicit typing on all public APIs.

**Error Handling:** Raise specific exceptions with context messages. Use pydantic for request/response validation.

**Database:** SQLAlchemy 2.0+ with async/await, using BaseEntity inheritance pattern.

**Architecture:** Services layer for business logic, models for data, api/routes for endpoints, compliance for audit trails.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** - Tests, linters, builds MUST pass
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

