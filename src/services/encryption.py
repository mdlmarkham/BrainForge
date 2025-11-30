"""Data encryption service for sensitive information at rest."""

import base64
import logging
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data at rest."""
    
    def __init__(self, encryption_key: str | None = None):
        """Initialize encryption service.
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, will use ENCRYPTION_KEY env var.
        """
        self.encryption_key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required for data encryption")
        
        # Derive a Fernet key from the provided key
        self.fernet = self._create_fernet(self.encryption_key)
    
    def _create_fernet(self, key: str) -> Fernet:
        """Create Fernet instance from base64-encoded key."""
        try:
            # If key is already base64-encoded Fernet key, use directly
            return Fernet(key.encode())
        except Exception:
            # Derive Fernet key from password using PBKDF2
            salt = b"brainforge_encryption_salt"  # Should be unique per deployment
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key_bytes = kdf.derive(key.encode())
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            return Fernet(fernet_key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data.
        
        Args:
            data: Plaintext data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext data
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise
    
    def encrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Encrypt all string values in a dictionary.
        
        Args:
            data: Dictionary with string values to encrypt
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted_dict = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted_dict[key] = self.encrypt(value)
            else:
                encrypted_dict[key] = value
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_data: dict[str, Any]) -> dict[str, Any]:
        """Decrypt all encrypted string values in a dictionary.
        
        Args:
            encrypted_data: Dictionary with encrypted values
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted_dict = {}
        for key, value in encrypted_data.items():
            if isinstance(value, str):
                try:
                    decrypted_dict[key] = self.decrypt(value)
                except Exception:
                    # If decryption fails, keep the original value (might not be encrypted)
                    decrypted_dict[key] = value
            else:
                decrypted_dict[key] = value
        return decrypted_dict


class KeyManagementService:
    """Service for managing encryption keys securely."""
    
    def __init__(self):
        self.key_storage_path = os.getenv("KEY_STORAGE_PATH", "/var/secrets/encryption_keys")
    
    def generate_key(self) -> str:
        """Generate a new Fernet encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()
    
    def rotate_key(self, old_key: str, new_key: str, encrypted_data: str) -> str:
        """Rotate encryption key for existing data.
        
        Args:
            old_key: Current encryption key
            new_key: New encryption key
            encrypted_data: Data encrypted with old key
            
        Returns:
            Data encrypted with new key
        """
        old_service = EncryptionService(old_key)
        new_service = EncryptionService(new_key)
        
        # Decrypt with old key, encrypt with new key
        decrypted_data = old_service.decrypt(encrypted_data)
        return new_service.encrypt(decrypted_data)
    
    def store_key(self, key_id: str, key: str) -> None:
        """Store encryption key securely.
        
        Args:
            key_id: Unique identifier for the key
            key: Encryption key to store
        """
        # In production, this should use a secure key management system
        # For now, store in environment-specific secure location
        key_file = os.path.join(self.key_storage_path, f"{key_id}.key")
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        with open(key_file, 'w') as f:
            f.write(key)
        
        # Set secure permissions
        os.chmod(key_file, 0o600)
    
    def load_key(self, key_id: str) -> str:
        """Load encryption key.
        
        Args:
            key_id: Unique identifier for the key
            
        Returns:
            Encryption key
        """
        key_file = os.path.join(self.key_storage_path, f"{key_id}.key")
        with open(key_file, 'r') as f:
            return f.read().strip()


# Global encryption service instance
encryption_service = EncryptionService()


def get_encryption_service() -> EncryptionService:
    """Get encryption service dependency."""
    return encryption_service