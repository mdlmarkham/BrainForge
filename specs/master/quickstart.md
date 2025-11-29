# Quickstart: Security & Quality Remediation

**Feature**: Security Remediation  
**Date**: 2025-11-29  
**Status**: Implementation Guide

## Prerequisites

### Dependencies Installation

```bash
# Install security dependencies
pip install python-jose[cryptography] passlib[bcrypt] python-multipart redis

# Add to requirements.txt
echo "python-jose[cryptography]==3.3.0" >> requirements.txt
echo "passlib[bcrypt]==1.7.4" >> requirements.txt
echo "python-multipart==0.0.6" >> requirements.txt
echo "redis==5.0.1" >> requirements.txt
```

### Environment Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Authentication
SECRET_KEY=your-super-secret-key-change-in-production
JWT_EXPIRE_MINUTES=1440

# Database
DATABASE_URL=postgresql://brainforge_user:secure_password@localhost:5432/brainforge
POSTGRES_USER=brainforge_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=brainforge

# Rate Limiting (optional)
REDIS_URL=redis://localhost:6379
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
```

## Implementation Steps

### Step 1: Database Migration

Create user authentication tables:

```bash
# Generate migration
alembic revision -m "Add user authentication tables"

# Apply migration
alembic upgrade head
```

### Step 2: User Model Implementation

Create [`src/models/orm/user.py`](src/models/orm/user.py:1):

```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from src.models.orm.base import Base

class User(Base):
    __tablename__ = "users"
    
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### Step 3: Authentication Service

Create [`src/services/auth.py`](src/services/auth.py:1):

```python
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
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Implementation continues...
```

### Step 4: API Dependencies

Update [`src/api/dependencies.py`](src/api/dependencies.py:1):

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import os

from src.config.database import get_session
from src.services.auth import AuthService
from src.models.orm.user import User

security = HTTPBearer()
auth_service = AuthService(secret_key=os.getenv("SECRET_KEY"))

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    # Implementation...
```

### Step 5: Authentication Routes

Create [`src/api/routes/auth.py`](src/api/routes/auth.py:1):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session
from src.services.auth import AuthService
from src.models.user import UserCreate, UserLogin, UserResponse
from src.models.orm.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_session)):
    # Implementation...
```

### Step 6: Rate Limiting Middleware

Create [`src/api/middleware/rate_limit.py`](src/api/middleware/rate_limit.py:1):

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import os

# Implementation for sliding window rate limiting
```

### Step 7: Update Existing Routes

Protect existing API routes by adding authentication dependency:

```python
from src.api.dependencies import get_current_user

@router.get("/protected-endpoint")
async def protected_endpoint(user: User = Depends(get_current_user)):
    # Existing implementation with user context
```

## Testing

### Unit Tests

Create [`tests/unit/test_auth.py`](tests/unit/test_auth.py:1):

```python
import pytest
from src.services.auth import AuthService
from src.models.user import UserCreate

@pytest.mark.asyncio
async def test_user_registration():
    # Test user creation and password hashing
    pass

@pytest.mark.asyncio
async def test_jwt_token_creation():
    # Test JWT token generation and validation
    pass
```

### Integration Tests

Create [`tests/integration/test_auth.py`](tests/integration/test_auth.py:1):

```python
import pytest
from fastapi.testclient import TestClient

def test_user_registration_flow(client: TestClient):
    # Test complete registration and login flow
    pass

def test_protected_endpoint_access(client: TestClient):
    # Test authentication requirement for protected endpoints
    pass
```

## Deployment Checklist

- [ ] Environment variables configured in production
- [ ] Database migration applied
- [ ] Secret key rotated from default
- [ ] Rate limiting configured appropriately
- [ ] SSL/TLS certificates installed
- [ ] Security headers configured
- [ ] Logging and monitoring enabled

## Security Best Practices

1. **Secret Management**: Use environment variables or secrets manager
2. **Token Expiration**: Set reasonable token expiration times
3. **Password Policy**: Enforce strong password requirements
4. **Rate Limiting**: Configure appropriate limits for your use case
5. **SSL/TLS**: Always use HTTPS in production
6. **Security Headers**: Implement CSP, HSTS, and other security headers

## Troubleshooting

### Common Issues

**Import Errors**: Ensure all imports use `src.` prefix
**Database Connection**: Verify DATABASE_URL environment variable
**JWT Validation**: Check SECRET_KEY configuration
**Rate Limiting**: Ensure Redis is running if using distributed limiting

### Debugging

Enable debug logging for authentication:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

After implementing security remediation:

1. **Monitor**: Set up security monitoring and alerting
2. **Audit**: Regular security audits and penetration testing
3. **Update**: Keep dependencies updated for security patches
4. **Enhance**: Consider additional security features like 2FA