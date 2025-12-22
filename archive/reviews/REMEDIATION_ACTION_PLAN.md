# BrainForge Security & Quality Remediation Action Plan

**Status:** Work in Progress
**Created:** 2025-11-29
**Target Completion:** After implementation of phases

---

## Phase 1: Critical Security Fixes (Target: 1-2 weeks)

### P1.1 Remove Hardcoded Credentials
**Priority:** CRITICAL (Blocks everything else)
**Effort:** 2 hours
**Files:**
- `docker-compose.yml` - Lines 6-9, 26, 41
- `config/database.env` - All credentials
- `src/api/routes/agent.py` - Line 15
- `src/services/embedding_generator.py` - Line 77

**Steps:**
1. Create `.env.example` template file with placeholder values
2. Update `.gitignore` to exclude `.env` files
3. Remove credentials from all version control files
4. Update Docker to use environment variables:
   ```yaml
   # Before
   POSTGRES_PASSWORD: brainforge_password

   # After
   POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
   ```
5. Update code to read from environment:
   ```python
   # Before
   agent_run_service = AgentRunService("postgresql://user:password@localhost/brainforge")

   # After
   database_url = os.getenv("DATABASE_URL")
   agent_run_service = AgentRunService(database_url)
   ```
6. Document in CONTRIBUTING.md how to set up local environment
7. Verify credentials are not in git history: `git log -S "password"`

**Definition of Done:**
- [ ] No plaintext credentials in any committed files
- [ ] `.env.example` in repository with instructions
- [ ] `.env` files in `.gitignore`
- [ ] CI/CD uses secrets manager
- [ ] Local setup documented
- [ ] All tests pass with environment-based config

---

### P1.2 Implement JWT Authentication
**Priority:** CRITICAL
**Effort:** 8 hours
**Files to Create/Modify:**
- Create `src/security/auth.py` - JWT token handling
- Create `src/models/user.py` - User model
- Modify `src/api/main.py` - Add auth dependencies
- Modify all route files - Add authentication checks

**Steps:**

1. **Install dependencies:**
   ```bash
   pip install python-jose[cryptography] passlib bcrypt
   ```

2. **Create user model:**
   ```python
   # src/models/user.py
   from sqlalchemy import Column, String
   from sqlalchemy.ext.asyncio import AsyncSession

   class User(Base):
       __tablename__ = "users"

       id = Column(UUID, primary_key=True, default=uuid4)
       username = Column(String, unique=True)
       email = Column(String, unique=True)
       hashed_password = Column(String)
       is_active = Column(Boolean, default=True)
   ```

3. **Create authentication service:**
   ```python
   # src/security/auth.py
   from datetime import datetime, timedelta
   from jose import JWTError, jwt
   from passlib.context import CryptContext

   class AuthService:
       def create_token(self, user_id: UUID) -> str:
           payload = {
               "sub": str(user_id),
               "exp": datetime.utcnow() + timedelta(hours=24)
           }
           return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

       def verify_token(self, token: str) -> UUID:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           return UUID(payload["sub"])
   ```

4. **Add to FastAPI:**
   ```python
   # src/api/dependencies.py
   from fastapi.security import HTTPBearer, HTTPAuthCredential
   from src.security.auth import AuthService

   security = HTTPBearer()

   async def get_current_user(credentials: HTTPAuthCredential = Depends(security)) -> User:
       user_id = auth_service.verify_token(credentials.credentials)
       return await get_user(user_id)
   ```

5. **Add to all protected routes:**
   ```python
   @router.get("/notes")
   async def list_notes(
       current_user: User = Depends(get_current_user),
       skip: int = 0,
       limit: int = 10
   ):
       # Filter notes by current_user.id
       stmt = select(Note).where(Note.user_id == current_user.id)
       notes = await session.execute(stmt)
       return notes.scalars().all()
   ```

6. **Create login endpoint:**
   ```python
   @router.post("/auth/login")
   async def login(username: str, password: str):
       user = await authenticate_user(username, password)
       token = auth_service.create_token(user.id)
       return {"access_token": token, "token_type": "bearer"}
   ```

**Definition of Done:**
- [ ] User model in database
- [ ] JWT token generation and verification working
- [ ] All protected endpoints require authentication
- [ ] Login endpoint functional
- [ ] Tests verify authentication enforcement
- [ ] Token expiration working
- [ ] Password hashing with bcrypt implemented

---

### P1.3 Add Rate Limiting
**Priority:** HIGH
**Effort:** 4 hours
**Files:**
- Modify `src/api/main.py`
- Add to `requirements.txt`

**Steps:**

1. **Install slowapi:**
   ```bash
   pip install slowapi
   ```

2. **Configure rate limiting:**
   ```python
   # src/api/main.py
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   ```

3. **Apply rate limits to endpoints:**
   ```python
   @router.post("/ingestion")
   @limiter.limit("5/minute")
   async def upload_pdf(
       request: Request,
       file: UploadFile,
       current_user: User = Depends(get_current_user)
   ):
       # Endpoint now limited to 5 uploads per minute per IP
   ```

4. **Set limits per endpoint type:**
   ```
   Authentication: 5 attempts per minute
   File Upload: 5 per minute
   Search: 30 per minute
   API: 100 per minute
   ```

**Definition of Done:**
- [ ] Slowapi installed and configured
- [ ] Rate limits applied to sensitive endpoints
- [ ] Rate limit exceeded returns 429 with retry-after
- [ ] Tests verify rate limiting works
- [ ] Monitoring in place for rate limit hits

---

### P1.4 Fix Path Traversal Vulnerabilities
**Priority:** HIGH
**Effort:** 1-2 hours
**Files:**
- `src/api/routes/obsidian.py` - Multiple endpoints
- Create `src/security/path_validation.py`

**Steps:**

1. **Create path validation utility:**
   ```python
   # src/security/path_validation.py
   from pathlib import Path
   from urllib.parse import unquote

   def validate_safe_path(filename: str, base_path: Path) -> Path:
       """Validate that filename doesn't escape base_path via traversal."""
       # Decode URL-encoded path
       decoded = unquote(filename)

       # Normalize and resolve
       safe_path = (base_path / decoded).resolve()

       # Ensure within base
       if not str(safe_path).startswith(str(base_path.resolve())):
           raise ValueError(f"Path traversal attempt: {filename}")

       return safe_path
   ```

2. **Update Obsidian routes:**
   ```python
   # Before
   @router.get("/notes/{filename:path}")
   async def get_obsidian_note(filename: str):
       note = await obsidian_service.get_note(filename)

   # After
   from src.security.path_validation import validate_safe_path

   @router.get("/notes/{filename:path}")
   async def get_obsidian_note(
       filename: str,
       current_user: User = Depends(get_current_user)
   ):
       safe_path = validate_safe_path(filename, Path("/vault/notes"))
       note = await obsidian_service.get_note(str(safe_path))
   ```

3. **Apply to all path parameters:**
   - `/vault` endpoint
   - `/notes/{filename}` endpoint
   - Any file operations

**Definition of Done:**
- [ ] Path validation utility created and tested
- [ ] All file path endpoints use validation
- [ ] Path traversal attempts blocked
- [ ] Tests verify validation with `../../` patterns

---

### P1.5 Replace MD5 with SHA-256
**Priority:** HIGH
**Effort:** 1 hour
**Files:**
- `src/services/embedding_generator.py` - Line 206
- `src/services/sync.py` - Line 75

**Steps:**

1. **Update embedding generator:**
   ```python
   # Before
   import hashlib
   hash_object = hashlib.md5(text.encode())

   # After
   import hashlib
   hash_object = hashlib.sha256(text.encode())
   ```

2. **Update sync service:**
   ```python
   # Before
   return hashlib.md5(content.encode('utf-8')).hexdigest()

   # After
   return hashlib.sha256(content.encode('utf-8')).hexdigest()
   ```

3. **Handle backward compatibility:**
   - Rehash existing content on next access
   - Or run migration: `python scripts/migrate_hashes.py`

**Definition of Done:**
- [ ] All MD5 calls replaced with SHA-256
- [ ] No MD5 found in codebase
- [ ] Tests pass with new hash algorithm
- [ ] Backward compatibility handled

---

### P1.6 Enable SSL/TLS Certificate Verification
**Priority:** HIGH
**Effort:** 30 minutes
**Files:**
- `src/services/obsidian.py` - Line 64

**Steps:**

1. **Remove verify=False:**
   ```python
   # Before
   self.client = httpx.AsyncClient(
       base_url=self.base_url,
       headers=headers,
       verify=False,  # INSECURE
       timeout=30.0
   )

   # After
   self.client = httpx.AsyncClient(
       base_url=self.base_url,
       headers=headers,
       # verify defaults to True (certificate validation enabled)
       timeout=30.0
   )
   ```

2. **For self-signed certificates (if needed):**
   ```python
   import ssl
   import certifi

   ctx = ssl.create_default_context(cafile=certifi.where())
   ctx.check_hostname = True
   ctx.verify_mode = ssl.CERT_REQUIRED

   self.client = httpx.AsyncClient(
       base_url=self.base_url,
       verify=ctx,
       timeout=30.0
   )
   ```

**Definition of Done:**
- [ ] SSL verification enabled by default
- [ ] Tests verify SSL validation is enforced
- [ ] Self-signed certificate handling documented
- [ ] No MITM vulnerabilities

---

## Phase 2: High-Priority Security (Target: Weeks 2-3)

### P2.1 Sanitize Error Responses
**Priority:** HIGH
**Effort:** 2 hours
**Files:** All route files

**Changes:**
```python
# Create exception handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An error occurred processing your request"}
    )
```

---

### P2.2 Input Validation & Sanitization
**Priority:** HIGH
**Effort:** 3 hours

**Steps:**
1. Sanitize file uploads
2. Validate search queries
3. Validate all query parameters
4. Implement file type verification (magic bytes)

---

### P2.3 Temporary File Cleanup
**Priority:** HIGH
**Effort:** 1-2 hours
**File:** `src/api/routes/ingestion.py`

**Changes:**
```python
async def cleanup_temp_file(file_path: str):
    try:
        os.unlink(file_path)
    except OSError:
        logger.warning(f"Failed to cleanup temp file: {file_path}")

async def process_with_cleanup(task_id, file_path):
    try:
        await ingestion_service.process_pdf_task(task_id, file_path)
    finally:
        await cleanup_temp_file(file_path)
```

---

### P2.4 Implement RBAC (Role-Based Access Control)
**Priority:** MEDIUM-HIGH
**Effort:** 4 hours

**Steps:**
1. Add Role model to database
2. Implement permission checking
3. Add role validation to protected endpoints

---

## Phase 3: Code Quality (Target: Week 3-4)

### P3.1 Fix Import Paths
**Priority:** HIGH (Affects functionality)
**Effort:** 30 minutes
**Files:**
- `src/services/pdf_processor.py`
- `src/services/ingestion_service.py`
- `src/api/routes/ingestion.py`

**Changes:**
```python
# Change all relative imports to absolute
from models.pdf_metadata import PDFMetadataCreate
# TO
from src.models.pdf_metadata import PDFMetadataCreate
```

---

### P3.2 Add Type Hints to __init__ Methods
**Priority:** MEDIUM
**Effort:** 1-2 hours

**Pattern:**
```python
def __init__(self, database_url: str) -> None:
    """Initialize service with database URL.

    Args:
        database_url: PostgreSQL connection string
    """
    self.database_url = database_url
```

---

### P3.3 Fix N+1 Query Problems
**Priority:** MEDIUM
**Effort:** 4 hours
**File:** `src/services/semantic_search.py`

**Changes:**
```python
# Before
for embedding, distance in vector_results:
    note = await self.database_service.get_note(embedding.note_id)

# After
note_ids = [e.note_id for e, _ in vector_results]
notes = await self.database_service.get_notes_bulk(note_ids)
```

---

### P3.4 Refactor Long Functions
**Priority:** MEDIUM
**Effort:** 4 hours
**Files:**
- `src/services/sync.py:sync_notes()`
- `src/services/ingestion_service.py:process_pdf_task()`

---

### P3.5 Increase Test Coverage
**Priority:** MEDIUM
**Effort:** 12 hours
**Target:** Add tests for:
- embedding_generator.py (0% coverage)
- database.py (0% coverage)
- All error paths
- N+1 query performance

---

## Phase 4: Compliance & Advanced (Target: Week 4+)

### P4.1 Data Encryption at Rest
**Priority:** MEDIUM
**Effort:** 12 hours

### P4.2 GDPR Data Deletion
**Priority:** MEDIUM
**Effort:** 6 hours

### P4.3 Structured Logging
**Priority:** MEDIUM
**Effort:** 6 hours

### P4.4 Performance Optimization
**Priority:** LOW
**Effort:** 8 hours

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit -v --cov=src
```

### Security Tests
```bash
# Run bandit for security issues
bandit -r src/

# Run safety for dependency vulnerabilities
safety check
```

### Integration Tests
```bash
pytest tests/integration -v
```

### Manual Security Testing
- [ ] OWASP Top 10 checklist
- [ ] Penetration testing
- [ ] Load testing with rate limits
- [ ] Path traversal fuzzing

---

## Definition of Done for All Phases

- [ ] All tests pass (unit, integration, security)
- [ ] Code review approved
- [ ] Security checklist completed
- [ ] Documentation updated
- [ ] No new security warnings from tools
- [ ] Performance benchmarks maintained
- [ ] Deployment process documented

---

## Success Metrics

After Phase 1 (Critical):
- ✓ Zero hardcoded credentials in repository
- ✓ All endpoints require authentication
- ✓ No rate limiting errors in testing
- ✓ No path traversal exploits possible

After Phase 2 (High-Priority):
- ✓ No stack traces in error responses
- ✓ All file uploads validated
- ✓ Temp files cleaned up
- ✓ RBAC fully implemented

After Phase 3 (Code Quality):
- ✓ All imports working correctly
- ✓ 100% of public methods typed
- ✓ Zero N+1 queries
- ✓ Test coverage ≥ 75%

After Phase 4 (Compliance):
- ✓ Data encrypted at rest
- ✓ GDPR delete endpoint functional
- ✓ Structured JSON logging
- ✓ Performance optimized

---

## Rollback Plan

If critical issues found during implementation:
1. Create new feature branch from current branch
2. Revert problematic commit
3. Document issue and workaround
4. Create new PR with fix
5. Review and test thoroughly before merge

---

## Documentation Updates

Update these files as fixes are completed:
- [ ] README.md - Add security section
- [ ] CONTRIBUTING.md - Add security checklist
- [ ] docs/architecture.md - Update with auth design
- [ ] docs/deployment.md - Add security configuration
- [ ] SECURITY.md - Create security policy document

---

**Last Updated:** 2025-11-29
**Next Review:** After Phase 1 completion
**Owner:** Security Team
