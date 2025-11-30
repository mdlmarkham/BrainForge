"""File upload validation and security utilities."""

import hashlib
import os
from pathlib import Path

import magic
from fastapi import HTTPException, UploadFile, status


class FileValidator:
    """Validate file uploads for security and integrity."""

    def __init__(self):
        # Allowed file types and their MIME types
        self.allowed_types = {
            'pdf': ['application/pdf'],
            'txt': ['text/plain'],
            'md': ['text/markdown', 'text/plain'],
            'json': ['application/json'],
        }

        # Maximum file sizes (in bytes)
        self.max_sizes = {
            'pdf': 100 * 1024 * 1024,  # 100MB
            'txt': 10 * 1024 * 1024,   # 10MB
            'md': 10 * 1024 * 1024,    # 10MB
            'json': 5 * 1024 * 1024,   # 5MB
        }

        # File extension to type mapping
        self.extension_map = {
            '.pdf': 'pdf',
            '.txt': 'txt',
            '.md': 'md',
            '.json': 'json',
        }

    async def validate_upload_file(self, file: UploadFile, allowed_types: list[str] | None = None) -> tuple[str, str]:
        """Validate an uploaded file for security.
        
        Args:
            file: The uploaded file
            allowed_types: List of allowed file types (e.g., ['pdf', 'txt'])
            
        Returns:
            Tuple of (file_type, file_hash)
            
        Raises:
            HTTPException: If validation fails
        """
        if allowed_types is None:
            allowed_types = list(self.allowed_types.keys())

        # Check file size
        file_size = file.size or 0
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Determine file type from extension
        file_extension = Path(file.filename).suffix.lower() if file.filename else ''
        file_type = self.extension_map.get(file_extension)

        if not file_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}"
            )

        if file_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_type} not allowed for this endpoint"
            )

        # Check file size against limits
        max_size = self.max_sizes.get(file_type, 10 * 1024 * 1024)  # Default 10MB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_size // (1024 * 1024)}MB"
            )

        # Read file content for MIME type validation
        content = await file.read()

        # Reset file pointer for further processing
        await file.seek(0)

        # Validate MIME type
        mime_type = self._get_mime_type(content, file.filename)
        allowed_mime_types = self.allowed_types.get(file_type, [])

        if mime_type not in allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File MIME type {mime_type} does not match expected type for {file_type}"
            )

        # Calculate file hash for integrity checking
        file_hash = self._calculate_file_hash(content)

        # Check for malicious content patterns
        self._check_malicious_content(content, file_type)

        return file_type, file_hash

    def _get_mime_type(self, content: bytes, filename: str) -> str:
        """Get MIME type using python-magic."""
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(content[:1024])  # Check first 1KB
            return mime_type
        except Exception:
            # Fallback to filename extension
            extension = Path(filename).suffix.lower()
            if extension == '.pdf':
                return 'application/pdf'
            elif extension == '.txt':
                return 'text/plain'
            elif extension == '.md':
                return 'text/markdown'
            elif extension == '.json':
                return 'application/json'
            else:
                return 'application/octet-stream'

    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

    def _check_malicious_content(self, content: bytes, file_type: str) -> None:
        """Check for malicious content patterns."""
        content_str = content.decode('utf-8', errors='ignore') if file_type in ['txt', 'md', 'json'] else ''

        # Check for script tags in text files
        if file_type in ['txt', 'md', 'json']:
            script_patterns = [
                r'<script[^>]*>',
                r'javascript:',
                r'on\w+\s*=',
            ]

            for pattern in script_patterns:
                import re
                if re.search(pattern, content_str, re.IGNORECASE):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File contains potentially malicious content"
                    )

        # Check for PDF-specific threats
        if file_type == 'pdf':
            # Check for embedded JavaScript in PDF
            if b'/JavaScript' in content or b'/JS' in content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF contains embedded JavaScript which is not allowed"
                )

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and injection."""
        # Remove path components
        filename = Path(filename).name

        # Remove potentially dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit filename length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext

        return filename


# Global file validator instance
file_validator = FileValidator()
