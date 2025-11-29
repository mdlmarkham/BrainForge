"""Unit tests for authentication service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from src.services.auth import AuthService
from src.models.user import UserCreate
from src.models.orm.user import User


class TestAuthService:
    """Test authentication service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.auth_service = AuthService(secret_key="test-secret-key")
        self.mock_session = AsyncMock()

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = self.auth_service.hash_password(password)
        
        # Should be different from original
        assert hashed != password
        # Should be a string
        assert isinstance(hashed, str)
        # Should be verifiable
        assert self.auth_service.verify_password(password, hashed)

    def test_verify_password(self):
        """Test password verification."""
        password = "test_password_123"
        hashed = self.auth_service.hash_password(password)
        
        # Correct password should verify
        assert self.auth_service.verify_password(password, hashed)
        # Wrong password should not verify
        assert not self.auth_service.verify_password("wrong_password", hashed)

    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        token = self.auth_service.create_access_token(user_id)
        
        # Should be a string
        assert isinstance(token, str)
        # Should be verifiable
        verified_id = self.auth_service.verify_token(token)
        assert verified_id == user_id

    def test_verify_token(self):
        """Test JWT token verification."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        token = self.auth_service.create_access_token(user_id)
        
        # Valid token should return user ID
        verified_id = self.auth_service.verify_token(token)
        assert verified_id == user_id
        
        # Invalid token should return None
        assert self.auth_service.verify_token("invalid_token") is None

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation."""
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123"
        )
        
        # Mock session to return no existing user
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Mock session commit and refresh
        self.mock_session.commit = AsyncMock()
        self.mock_session.refresh = AsyncMock()
        
        user = await self.auth_service.create_user(self.mock_session, user_create)
        
        # Should create user with hashed password
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password != "TestPassword123"  # Should be hashed
        assert self.auth_service.verify_password("TestPassword123", user.hashed_password)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username."""
        user_create = UserCreate(
            username="existinguser",
            email="test@example.com",
            password="TestPassword123"
        )
        
        # Mock existing user with same username
        existing_user = User(
            username="existinguser",
            email="existing@example.com",
            hashed_password="hashed"
        )
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = existing_user
        
        with pytest.raises(ValueError, match="Username already exists"):
            await self.auth_service.create_user(self.mock_session, user_create)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email."""
        user_create = UserCreate(
            username="newuser",
            email="existing@example.com",
            password="TestPassword123"
        )
        
        # Mock existing user with same email
        existing_user = User(
            username="existinguser",
            email="existing@example.com",
            hashed_password="hashed"
        )
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = existing_user
        
        with pytest.raises(ValueError, match="Email already exists"):
            await self.auth_service.create_user(self.mock_session, user_create)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        username = "testuser"
        password = "TestPassword123"
        
        # Mock user with correct password
        mock_user = User(
            username=username,
            email="test@example.com",
            hashed_password=self.auth_service.hash_password(password)
        )
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        user = await self.auth_service.authenticate_user(self.mock_session, username, password)
        
        assert user == mock_user

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        username = "testuser"
        correct_password = "TestPassword123"
        wrong_password = "WrongPassword123"
        
        # Mock user with correct password
        mock_user = User(
            username=username,
            email="test@example.com",
            hashed_password=self.auth_service.hash_password(correct_password)
        )
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        user = await self.auth_service.authenticate_user(self.mock_session, username, wrong_password)
        
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user."""
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        user = await self.auth_service.authenticate_user(self.mock_session, "nonexistent", "password")
        
        assert user is None