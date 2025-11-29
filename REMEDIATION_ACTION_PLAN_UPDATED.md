# BrainForge Security & Quality Remediation Action Plan - UPDATED
**Date:** 2025-11-29
**Status:** Updated with detailed steps and current state analysis
**Priority Level:** CRITICAL - Must complete Phase 1 before any deployment
**Target Timeline:** 2 weeks for full production readiness

---

## Quick Reference: Critical Path

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: CRITICAL SECURITY FIXES (14 hours)           │
│  ═════════════════════════════════════════════════════  │
│  [P1.1] Fix Import Paths               (0.5h) - START   │
│  [P1.2] Remove Hardcoded Credentials   (1h)            │
│  [P1.3] Add JWT Authentication         (8h) - LARGEST   │
│  [P1.4] Fix Path Traversal             (2h)            │
│  [P1.5] Replace MD5 Hashing            (1h)            │
│  [P1.6] Enable SSL Verification        (0.5h)          │
│  [P1.7] Add Rate Limiting              (2h)            │
│  Total: 14 hours                                        │
│  Effort: 2 days of focused development                 │
└─────────────────────────────────────────────────────────┘
```

---

## PHASE 1: CRITICAL SECURITY FIXES

### P1.1: Fix Import Path Errors (30 minutes)

**Status:** 🔴 CRITICAL - Application won't run without this

**Files to Fix:**
```
src/services/pdf_processor.py       (Lines 8-9)
src/services/ingestion_service.py   (Lines 14-23)
src/api/routes/ingestion.py         (Lines 13-14)
src/services/base.py                (Line 9)
```

**Implementation Steps:**

1. **Update pdf_processor.py imports:**
```python
# BEFORE
from models.pdf_metadata import PDFMetadataCreate
from models.pdf_processing_result import PDFProcessingResultCreate

# AFTER
from src.models.pdf_metadata import PDFMetadataCreate
from src.models.pdf_processing_result import PDFProcessingResultCreate
```

2. **Update ingestion_service.py imports:**
```python
# BEFORE (10 imports to fix)
from models.ingestion import ContentType
from models.content_source import ContentSource
# ... etc

# AFTER
from src.models.ingestion import ContentType
from src.models.content_source import ContentSource
```

3. **Update api/routes/ingestion.py imports:**
```python
# BEFORE
from models.ingestion import ContentType, IngestionTask
from services.ingestion_service import IngestionService

# AFTER
from src.models.ingestion import ContentType, IngestionTask
from src.services.ingestion_service import IngestionService
```

4. **Update services/base.py imports:**
```python
# BEFORE
from models.orm.base import Base

# AFTER
from src.models.orm.base import Base
```

5. **Verify all imports work:**
```bash
python -m py_compile src/services/pdf_processor.py
python -m py_compile src/services/ingestion_service.py
python -m py_compile src/api/routes/ingestion.py
python -m py_compile src/services/base.py

# Or run the app
uvicorn src.api.main:app --reload
```

**Definition of Done:**
- [ ] All 4 files updated with correct import paths
- [ ] Python can compile all modules without ImportError
- [ ] Application starts without import errors
- [ ] Tests pass

**Commit Message:**
```
fix: Correct Python import paths in services and routes

- Fix relative imports to use src. prefix
- Update imports in pdf_processor.py (lines 8-9)
- Update imports in ingestion_service.py (lines 14-23)
- Update imports in api/routes/ingestion.py (lines 13-14)
- Update imports in services/base.py (line 9)

Fixes ImportError runtime failures when modules are loaded.
```

---

### P1.2: Remove Hardcoded Credentials (1 hour)

**Status:** 🔴 CRITICAL - Database passwords visible in repo

**Current Hardcoded Credentials:**

| File | Location | Credential |
|------|----------|-----------|
| docker-compose.yml | Line 9 | POSTGRES_PASSWORD |
| docker-compose.yml | Line 26 | DATABASE_URL |
| config/database.env | All | All environment variables |
| src/api/routes/agent.py | Line 15 | Database URL in code |

**Implementation Steps:**

1. **Create .env.example template:**
```bash
cat > .env.example << 'EOF'
# PostgreSQL Configuration
POSTGRES_USER=brainforge_user
POSTGRES_PASSWORD=<change-me-in-production>
POSTGRES_DB=brainforge
DATABASE_URL=postgresql://brainforge_user:<change-me>@localhost:5432/brainforge

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO

# OpenAI Configuration
OPENAI_API_KEY=<your-api-key-here>

# Obsidian Configuration
OBSIDIAN_API_URL=http://localhost:27124
OBSIDIAN_API_TOKEN=<your-token-here>
EOF
```

2. **Update .gitignore:**
```bash
# Add to .gitignore if not already present
.env
.env.local
.env.*.local
config/database.env
```

3. **Update docker-compose.yml:**
```yaml
# BEFORE
version: '3.8'
services:
  database:
    environment:
      POSTGRES_PASSWORD: brainforge_password  # ❌ REMOVE

# AFTER
version: '3.8'
services:
  database:
    env_file:
      - .env
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # From .env
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_DB: ${POSTGRES_DB}
```

4. **Update src/api/routes/agent.py (Line 15):**
```python
# BEFORE
agent_run_service = AgentRunService("postgresql://user:password@localhost/brainforge")

# AFTER
import os
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")
agent_run_service = AgentRunService(database_url)
```

5. **Create config/database.env from template:**
```bash
cp .env.example .env

# Edit .env with actual development values
# NEVER commit .env to git
```

6. **Verify credentials are removed:**
```bash
# Check no passwords in docker-compose.yml
grep -n "password\|POSTGRES" docker-compose.yml | grep -v "\${"

# Check no passwords in Python files
grep -rn "postgresql://.*:.*@" src/ | grep -v "os.getenv\|environment\|template"

# Check git history (if repo is older)
git log -S "password" -- docker-compose.yml
```

**Definition of Done:**
- [ ] .env.example created with template values
- [ ] .env added to .gitignore
- [ ] docker-compose.yml uses environment variable references
- [ ] src/api/routes/agent.py uses os.getenv()
- [ ] No plaintext credentials visible in code
- [ ] Application starts with environment variables
- [ ] Tests pass with configured environment

**Commit Message:**
```
security: Remove hardcoded credentials from codebase

- Create .env.example with template configuration
- Update docker-compose.yml to use env variables
- Update agent.py to read DATABASE_URL from environment
- Add .env to .gitignore
- Remove plaintext POSTGRES_PASSWORD from docker-compose.yml

This prevents credential exposure in version control.
Developers must set up .env file locally before running.
Production deployment must use secrets manager (AWS Secrets, Vault, etc).
```

---

### P1.3: Implement JWT Authentication (8 hours)

**Status:** 🔴 CRITICAL - Zero authentication currently enforced

**This is the largest task. Break into sub-tasks:**

#### P1.3.1: Database Schema & User Model (1.5 hours)

**Create migration:**
```bash
alembic revision -m "Add user authentication tables"
```

**Migration file (alembic/versions/003_add_user_auth.py):**
```python
def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade() -> None:
    op.drop_table('users')
```

**Create ORM model:**
```python
# src/models/orm/user.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from src.models.orm.base import Base

class User(Base):
    __tablename__ = "users"

    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"
```

**Create Pydantic models:**
```python
# src/models/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True
```

**Definition of Done:**
- [ ] Migration creates users table
- [ ] ORM User model defined
- [ ] Pydantic user models defined
- [ ] Migration runs successfully

---

#### P1.3.2: Authentication Service (2 hours)

**Create authentication service:**
```python
# src/services/auth.py
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.orm.user import User
from src.models.user import UserCreate

class AuthService:
    """JWT-based authentication service."""

    def __init__(self, secret_key: str, algorithm: str = "HS256", expire_minutes: int = 1440):
        """Initialize authentication service.

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT signing algorithm
            expire_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[UUID]:
        """Verify JWT token and return user ID."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            return UUID(user_id)
        except JWTError:
            return None

    async def create_user(
        self,
        session: AsyncSession,
        user_create: UserCreate
    ) -> User:
        """Create new user with hashed password."""
        hashed_password = self.hash_password(user_create.password)
        user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def authenticate_user(
        self,
        session: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user by username and password."""
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(password, user.hashed_password):
            return None

        return user

    async def get_user_by_id(self, session: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return await session.get(User, user_id)
```

**Install dependencies:**
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

**Add to requirements.txt:**
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

**Definition of Done:**
- [ ] AuthService implemented with all methods
- [ ] Password hashing with bcrypt working
- [ ] JWT token generation/verification working
- [ ] Dependencies installed
- [ ] Unit tests pass

---

#### P1.3.3: Dependency Injection & Middleware (2 hours)

**Update src/api/dependencies.py:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredential
from sqlalchemy.ext.asyncio import AsyncSession
import os

from src.config.database import get_session
from src.services.auth import AuthService
from src.models.orm.user import User

security = HTTPBearer()
auth_service = AuthService(secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod"))

async def get_current_user(
    credentials: HTTPAuthCredential = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user_id = auth_service.verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(session, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
```

**Update src/api/main.py:**
```python
# Add secret key to environment
if "SECRET_KEY" not in os.environ:
    import warnings
    warnings.warn("SECRET_KEY not set - using development default. SET THIS IN PRODUCTION!")
    os.environ["SECRET_KEY"] = "dev-secret-key-change-in-prod"

# Add authentication routes
from src.api.routes import auth

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
```

**Create authentication routes:**
```python
# src/api/routes/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import get_session, auth_service, get_current_user
from src.models.user import UserCreate, UserLogin, UserResponse
from src.models.orm.user import User

router = APIRouter()

@router.post("/auth/register", response_model=UserResponse)
async def register(
    user_create: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Register a new user."""
    try:
        return await auth_service.create_user(session, user_create)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered"
        )

@router.post("/auth/login")
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_session),
):
    """Login user and return JWT token."""
    user = await auth_service.authenticate_user(
        session,
        credentials.username,
        credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    token = auth_service.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current authenticated user info."""
    return current_user
```

**Definition of Done:**
- [ ] Authentication dependencies implemented
- [ ] Login/register endpoints working
- [ ] Token generation verified
- [ ] Token validation tested
- [ ] Current user endpoint working

---

#### P1.3.4: Protect All Endpoints (2 hours)

**Update all route files to require authentication:**

```python
# EXAMPLE: src/api/routes/notes.py

from src.api.dependencies import get_current_user
from src.models.orm.user import User

@router.get("/notes")
async def list_notes(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # ← ADD THIS
    skip: int = 0,
    limit: int = 10,
):
    """List notes for current user."""
    # Filter by user
    stmt = select(Note).where(
        Note.user_id == current_user.id  # ← USER ISOLATION
    ).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/notes", response_model=NoteResponse)
async def create_note(
    note_create: NoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # ← ADD THIS
):
    """Create note for current user."""
    note = Note(
        **note_create.dict(),
        user_id=current_user.id,  # ← ASSOCIATE WITH USER
    )
    session.add(note)
    await session.commit()
    return note
```

**Apply to ALL route files:**
- src/api/routes/notes.py (all endpoints)
- src/api/routes/search.py (all endpoints)
- src/api/routes/ingestion.py (all endpoints)
- src/api/routes/agent.py (all endpoints)
- src/api/routes/obsidian.py (all endpoints)
- src/api/routes/vault.py (all endpoints)

**Definition of Done:**
- [ ] All endpoints require authentication
- [ ] User data isolated by user_id
- [ ] Tests verify authentication enforcement
- [ ] Unauthenticated requests return 401

---

#### P1.3.5: Update Tests (1 hour)

**Create auth tests:**
```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "secure-password-123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test user login."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "secure-password-123"
        }
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "secure-password-123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_protected_endpoint_without_auth(client: AsyncClient):
    """Test that protected endpoints require authentication."""
    response = await client.get("/api/v1/notes")
    assert response.status_code == 403  # Forbidden without auth
```

**Update existing tests to authenticate:**
```python
# In test fixtures
@pytest.fixture
async def authenticated_client(client: AsyncClient):
    """Create client with authenticated user."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "password123"}
    )

    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

**Definition of Done:**
- [ ] Authentication tests passing
- [ ] Protected endpoint tests passing
- [ ] User isolation verified in tests
- [ ] All existing tests updated to use authenticated_client

---

### P1.4: Fix Path Traversal Vulnerabilities (2 hours)

**Create path validation utility:**

```python
# src/security/path_validator.py
from pathlib import Path
from urllib.parse import unquote
from fastapi import HTTPException

def validate_safe_path(filename: str, base_path: Path) -> Path:
    """Validate that filename doesn't escape base_path via traversal.

    Args:
        filename: User-provided filename (may be URL-encoded)
        base_path: Base directory path

    Returns:
        Safe Path object within base_path

    Raises:
        HTTPException: If path traversal attempt detected
    """
    # Decode URL-encoded path
    decoded = unquote(filename)

    # Prevent null bytes
    if '\x00' in decoded:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Normalize and resolve to absolute path
    try:
        safe_path = (base_path / decoded).resolve()
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Ensure resolved path is within base_path
    try:
        safe_path.relative_to(base_path.resolve())
    except ValueError:
        # Path is outside base_path (traversal attempt)
        raise HTTPException(status_code=403, detail="Access denied")

    return safe_path
```

**Update obsidian.py routes:**

```python
# src/api/routes/obsidian.py
from src.security.path_validator import validate_safe_path
from pathlib import Path

VAULT_BASE_PATH = Path("/vault/notes")  # Configure as needed

@router.get("/notes/{filename:path}")
async def get_obsidian_note(
    filename: str,
    as_json: bool = False,
    current_user: User = Depends(get_current_user),
    obsidian_service: ObsidianService = Depends(get_obsidian_service),
) -> NoteResponse:
    """Get Obsidian note by validated path."""
    # Validate path is within vault
    safe_path = validate_safe_path(filename, VAULT_BASE_PATH)

    # Use validated path
    note = await obsidian_service.get_note(str(safe_path), as_json=as_json)
    return note

@router.post("/notes/{filename:path}")
async def create_or_append_note(
    filename: str,
    content: str,
    current_user: User = Depends(get_current_user),
    obsidian_service: ObsidianService = Depends(get_obsidian_service),
) -> NoteResponse:
    """Create or append to Obsidian note with validated path."""
    safe_path = validate_safe_path(filename, VAULT_BASE_PATH)

    note = await obsidian_service.create_or_append(str(safe_path), content)
    return note

@router.get("/vault")
async def list_vault_files(
    directory: str = "",
    current_user: User = Depends(get_current_user),
    obsidian_service: ObsidianService = Depends(get_obsidian_service),
) -> VaultFilesResponse:
    """List files in vault directory with validated path."""
    safe_path = validate_safe_path(directory, VAULT_BASE_PATH)

    files = await obsidian_service.list_vault_files(str(safe_path))
    return files
```

**Add tests:**

```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
from src.security.path_validator import validate_safe_path
from pathlib import Path

def test_path_traversal_blocked():
    """Test that path traversal attempts are blocked."""
    base_path = Path("/vault")

    # These should raise HTTPException
    with pytest.raises(HTTPException):
        validate_safe_path("../../etc/passwd", base_path)

    with pytest.raises(HTTPException):
        validate_safe_path("../../../.env", base_path)

def test_valid_paths_allowed():
    """Test that legitimate paths are allowed."""
    base_path = Path("/vault")

    # These should succeed
    result = validate_safe_path("notes/file.md", base_path)
    assert result.name == "file.md"

    result = validate_safe_path("folder/subfolder/file.md", base_path)
    assert result.name == "file.md"

@pytest.mark.asyncio
async def test_obsidian_path_validation(client: AsyncClient, auth_token: str):
    """Test that obsidian routes validate paths."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Traversal attempt should fail
    response = await client.get(
        "/api/v1/obsidian/notes/../../config/database.env",
        headers=headers
    )
    assert response.status_code == 403
```

**Definition of Done:**
- [ ] Path validator utility created and tested
- [ ] All obsidian routes use path validation
- [ ] Path traversal tests passing
- [ ] No path traversal exploits possible

**Commit Message:**
```
security: Add path traversal protection to Obsidian integration

- Create path validation utility (path_validator.py)
- Validate all file path parameters before use
- Prevent ../../../ traversal patterns
- Add comprehensive path validation tests
- Apply validation to all obsidian.py endpoints

Prevents arbitrary file read/write via path traversal.
```

---

### P1.5: Replace MD5 with SHA-256 (1 hour)

**Update sync.py:**

```python
# BEFORE (Line 75)
import hashlib

def _calculate_content_hash(self, content: str) -> str:
    """Calculate hash of note content for change detection."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# AFTER
import hashlib

def _calculate_content_hash(self, content: str) -> str:
    """Calculate hash of note content for change detection."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

**Update embedding_generator.py:**

```python
# BEFORE (Line 206)
hash_object = hashlib.md5(text.encode())

# AFTER
hash_object = hashlib.sha256(text.encode())
```

**Handle backward compatibility:**

```python
# Add migration note in code
def _calculate_content_hash(self, content: str) -> str:
    """Calculate hash of note content for change detection.

    NOTE: Changed from MD5 (cryptographically broken) to SHA-256.
    Existing MD5 hashes will be recalculated on next sync.
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

**Verify no MD5 remains:**

```bash
grep -rn "md5\|MD5" src/ --include="*.py" | grep -v "test\|comment"
# Should return empty result
```

**Definition of Done:**
- [ ] All MD5 calls replaced with SHA-256
- [ ] No MD5 found in codebase
- [ ] Tests pass with new hash algorithm
- [ ] Backward compatibility handled

**Commit Message:**
```
security: Replace MD5 with SHA-256 hashing

- Change _calculate_content_hash() to use SHA-256 instead of MD5
- Update fallback embedding hash generation to SHA-256
- MD5 is cryptographically broken and unsuitable for integrity checking

This improves cryptographic security posture.
```

---

### P1.6: Enable SSL Certificate Verification (30 minutes)

**Update obsidian.py:**

```python
# BEFORE (Line 64)
self.client = httpx.AsyncClient(
    base_url=self.base_url,
    headers=headers,
    verify=False,  # ❌ DISABLES SECURITY!
    timeout=30.0
)

# AFTER - Option 1: Default verification (simplest)
self.client = httpx.AsyncClient(
    base_url=self.base_url,
    headers=headers,
    # verify defaults to True, validates certificates
    timeout=30.0
)

# AFTER - Option 2: Custom certificate path (if self-signed needed)
import ssl
import certifi

ctx = ssl.create_default_context(cafile=certifi.where())
ctx.check_hostname = True
ctx.verify_mode = ssl.CERT_REQUIRED

self.client = httpx.AsyncClient(
    base_url=self.base_url,
    headers=headers,
    verify=ctx,
    timeout=30.0
)

# AFTER - Option 3: Self-signed certificate support (documented)
"""
For self-signed certificates in development:

1. Export the certificate from Obsidian
2. Store in config/certs/obsidian.pem
3. Use:
   verify=pathlib.Path("config/certs/obsidian.pem")
"""
```

**Add configuration:**

```python
# src/config/security.py
import os
from pathlib import Path

OBSIDIAN_CERT_PATH = os.getenv("OBSIDIAN_CERT_PATH")
OBSIDIAN_VERIFY_SSL = os.getenv("OBSIDIAN_VERIFY_SSL", "true").lower() == "true"

def get_obsidian_verify_config():
    """Get SSL verification config for Obsidian API."""
    if not OBSIDIAN_VERIFY_SSL:
        raise ValueError("SSL verification must be enabled for security")

    if OBSIDIAN_CERT_PATH:
        return Path(OBSIDIAN_CERT_PATH)

    return True  # Default system cert bundle
```

**Update .env.example:**

```
# Obsidian Configuration
OBSIDIAN_API_URL=http://localhost:27124
OBSIDIAN_API_TOKEN=<your-token>
OBSIDIAN_VERIFY_SSL=true
# OBSIDIAN_CERT_PATH=/path/to/cert.pem  # Only if self-signed
```

**Add tests:**

```python
# tests/test_ssl_verification.py
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_ssl_verification_enabled():
    """Test that SSL verification is enabled by default."""
    from src.services.obsidian import ObsidianService

    service = ObsidianService()

    # Verify SSL is enabled (not False)
    assert service.client.verify is not False
    # Should be True or ssl.SSLContext object
```

**Definition of Done:**
- [ ] SSL verification enabled by default
- [ ] No verify=False in codebase
- [ ] Tests verify SSL is enabled
- [ ] Documentation for self-signed certificates
- [ ] No MITM vulnerabilities

**Commit Message:**
```
security: Enable SSL/TLS certificate verification

- Remove verify=False from Obsidian client
- Enable default SSL certificate validation
- Add configuration for custom certificate paths
- Add documentation for self-signed certificates
- Add tests verifying SSL verification is enabled

Prevents man-in-the-middle attacks on Obsidian API communication.
```

---

### P1.7: Implement Rate Limiting (2 hours)

**Install slowapi:**

```bash
pip install slowapi
```

**Add to requirements.txt:**
```
slowapi==0.1.9
```

**Configure rate limiting:**

```python
# src/api/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()

# Add exception handler for rate limit exceeded
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after,
        },
        headers={"Retry-After": str(exc.retry_after)},
    )

# Add limiter to app
app.state.limiter = limiter
```

**Apply rate limits to endpoints:**

```python
# src/api/routes/auth.py
from slowapi import Limiter

@router.post("/auth/register")
@limiter.limit("5/hour")  # 5 registrations per hour per IP
async def register(user_create: UserCreate, ...):
    """Register new user with rate limiting."""
    pass

@router.post("/auth/login")
@limiter.limit("10/minute")  # 10 login attempts per minute per IP
async def login(credentials: UserLogin, ...):
    """Login with rate limiting."""
    pass

# src/api/routes/ingestion.py
@router.post("/pdf")
@limiter.limit("5/minute")  # 5 PDF uploads per minute per IP
async def upload_pdf(file: UploadFile, ...):
    """Upload PDF with rate limiting."""
    pass

# src/api/routes/search.py
@router.post("/search")
@limiter.limit("30/minute")  # 30 searches per minute per IP
async def semantic_search(query: str, ...):
    """Search with rate limiting."""
    pass
```

**Rate limiting strategy:**

| Endpoint Type | Limit | Rationale |
|---------------|-------|-----------|
| Authentication (login/register) | 5-10/minute | Prevent brute force |
| File uploads | 5/minute | Prevent resource exhaustion |
| Search operations | 30/minute | Balance usability & resource use |
| API operations (generic) | 100/minute | Prevent DoS |
| Health check | Unlimited | Used by monitoring |

**Add tests:**

```python
# tests/test_rate_limiting.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limit_login():
    """Test rate limiting on login endpoint."""
    client = AsyncClient()

    # Make 11 login attempts (limit is 10/minute)
    for i in range(11):
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "user", "password": "password"}
        )

        if i < 10:
            assert response.status_code in [401, 400]  # Auth failure, not rate limit
        else:
            assert response.status_code == 429  # Rate limited

@pytest.mark.asyncio
async def test_rate_limit_upload():
    """Test rate limiting on file upload."""
    client = AsyncClient()

    # Make 6 upload attempts (limit is 5/minute)
    for i in range(6):
        response = await client.post(
            "/api/v1/ingestion/pdf",
            files={"file": ("test.pdf", b"fake pdf content")}
        )

        if i < 5:
            # Should fail for other reasons (auth, validation) not rate limit
            assert response.status_code != 429
        else:
            # Should be rate limited
            assert response.status_code == 429
```

**Definition of Done:**
- [ ] Slowapi installed and configured
- [ ] Rate limits applied to sensitive endpoints
- [ ] Rate limit exceeded returns 429 with Retry-After
- [ ] Tests verify rate limiting works
- [ ] Monitoring in place for rate limit hits

**Commit Message:**
```
security: Implement rate limiting on API endpoints

- Install slowapi for rate limiting
- Configure rate limits per endpoint type:
  - Auth endpoints: 5-10/minute (prevent brute force)
  - File uploads: 5/minute (prevent resource exhaustion)
  - Search: 30/minute (balance usability)
  - Generic API: 100/minute (prevent DoS)
- Add 429 Too Many Requests response with Retry-After header
- Add comprehensive rate limiting tests

Prevents brute force, resource exhaustion, and DoS attacks.
```

---

## Phase 1 Summary

**Total Effort:** 14 hours of focused development

**Critical Fixes:**
1. ✅ P1.1: Import paths fixed (0.5 hours)
2. ✅ P1.2: Credentials removed (1 hour)
3. ✅ P1.3: JWT authentication (8 hours)
4. ✅ P1.4: Path traversal fixed (2 hours)
5. ✅ P1.5: MD5 → SHA-256 (1 hour)
6. ✅ P1.6: SSL verification (0.5 hours)
7. ✅ P1.7: Rate limiting (2 hours)

**After Phase 1:**
- Application will start without import errors
- No plaintext credentials in codebase
- All endpoints require authentication
- Path traversal attacks blocked
- Cryptography secure (SHA-256+)
- SSL/TLS verification enabled
- Rate limiting prevents abuse

**Application Status:** Can be deployed to testing environment

**Next Phase:** Phase 2 (Input validation, error handling) - 8 hours

---

## Quick Git Checklist

Before each commit, verify:
```bash
# Check no credentials leaked
grep -r "password\|secret\|api.key" src/ config/ docker-compose.yml

# Check no plaintext in env files
git diff HEAD -- .env config/database.env

# Run tests
pytest tests/ -v

# Run linting
ruff check src/

# Run type checking
mypy src/
```

---

**Last Updated:** 2025-11-29
**Status:** Ready for implementation
**Next Review:** After Phase 1 completion
