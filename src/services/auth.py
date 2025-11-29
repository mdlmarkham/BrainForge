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
        # Check if username or email already exists
        stmt = select(User).where(
            (User.username == user_create.username) | (User.email == user_create.email)
        )
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.username == user_create.username:
                raise ValueError("Username already exists")
            else:
                raise ValueError("Email already exists")

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

    async def get_user_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        session: AsyncSession = Depends(get_db),
    ) -> User:
        """Get current authenticated user from JWT token."""
        from fastapi import HTTPException, status
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
        from src.api.dependencies import get_db
        
        token = credentials.credentials
        user_id = self.verify_token(token)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self.get_user_by_id(session, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return user