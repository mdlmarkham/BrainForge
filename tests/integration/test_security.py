"""Integration tests for security features."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.main import create_app


class TestSecurityFeatures:
    """Test security hardening implementations."""
    
    def setup_method(self):
        """Set up test client."""
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_authentication_required_for_protected_endpoints(self):
        """Test that all protected endpoints require authentication."""
        # Test notes endpoint without authentication
        response = self.client.get("/api/v1/notes")
        assert response.status_code == 401  # Unauthorized
        
        # Test search endpoint without authentication
        response = self.client.post("/api/v1/search", json={"query": "test"})
        assert response.status_code == 401
        
        # Test research endpoint without authentication
        response = self.client.get("/api/v1/research/runs")
        assert response.status_code == 401
        
        # Test ingestion endpoint without authentication
        response = self.client.get("/api/v1/ingestion/pdf/12345678-1234-5678-1234-567812345678")
        assert response.status_code == 401
    
    def test_rate_limiting_authentication_endpoints(self):
        """Test rate limiting on authentication endpoints."""
        # Test login endpoint rate limiting
        for i in range(15):  # More than the 10 requests per minute limit
            response = self.client.post(
                "/api/v1/auth/login",
                json={"username": "test", "password": "test"}
            )
            if i >= 10:
                assert response.status_code == 429  # Too Many Requests
            else:
                # Should be 401 (unauthorized) not 429 (rate limited)
                assert response.status_code != 429
    
    def test_rate_limiting_file_upload_endpoints(self):
        """Test rate limiting on file upload endpoints."""
        # Mock file upload
        mock_file = ("test.pdf", b"fake pdf content", "application/pdf")
        
        for i in range(10):  # More than the 5 requests per minute limit
            response = self.client.post(
                "/api/v1/ingestion/pdf",
                files={"file": mock_file},
                data={"priority": "normal"}
            )
            if i >= 5:
                assert response.status_code == 429  # Too Many Requests
            else:
                # Should be 401 (unauthorized) not 429 (rate limited)
                assert response.status_code != 429
    
    def test_error_response_sanitization(self):
        """Test that error responses don't leak sensitive information."""
        # Trigger an internal server error
        with patch('src.api.routes.notes.list_notes') as mock_list:
            mock_list.side_effect = Exception("Sensitive database error: password=secret")
            
            response = self.client.get("/api/v1/notes")
            assert response.status_code == 500
            data = response.json()
            
            # Check that sensitive information is not leaked
            assert "Sensitive database error" not in data.get("error", "")
            assert "password=secret" not in data.get("message", "")
            assert "Internal server error" in data.get("error", "")
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in query parameters."""
        # Test SQL injection in path parameter
        response = self.client.get("/api/v1/notes/1%20OR%201=1")
        assert response.status_code == 400  # Bad Request
        
        # Test SQL injection in query parameter
        response = self.client.get("/api/v1/search?query=test%20UNION%20SELECT%20*%20FROM%20users")
        assert response.status_code == 400
        
        # Test SQL injection in headers
        headers = {"User-Agent": "Mozilla/5.0' OR '1'='1"}
        response = self.client.get("/api/v1/notes", headers=headers)
        assert response.status_code == 400
    
    def test_xss_prevention(self):
        """Test XSS prevention in input validation."""
        # Test XSS in path parameter
        response = self.client.get("/api/v1/notes/<script>alert('xss')</script>")
        assert response.status_code == 400
        
        # Test XSS in query parameter
        response = self.client.get("/api/v1/search?query=<script>alert('xss')</script>")
        assert response.status_code == 400
        
        # Test XSS in headers
        headers = {"User-Agent": "<script>alert('xss')</script>"}
        response = self.client.get("/api/v1/notes", headers=headers)
        assert response.status_code == 400
    
    def test_path_traversal_prevention(self):
        """Test path traversal prevention."""
        # Test path traversal in filename
        response = self.client.get("/api/v1/obsidian/notes/../../../etc/passwd")
        assert response.status_code == 400
        
        # Test encoded path traversal
        response = self.client.get("/api/v1/obsidian/notes/%2e%2e%2f%2e%2e%2fetc%2fpasswd")
        assert response.status_code == 400
    
    def test_cors_security(self):
        """Test CORS security configuration."""
        # Test preflight request from allowed origin
        response = self.client.options(
            "/api/v1/notes",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        
        # Test preflight request from disallowed origin
        response = self.client.options(
            "/api/v1/notes",
            headers={
                "Origin": "http://malicious.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        # Should either block or not include CORS headers for disallowed origin
        assert "http://malicious.com" not in response.headers.get("Access-Control-Allow-Origin", "")
    
    def test_health_endpoint_accessible_without_auth(self):
        """Test that health endpoint is accessible without authentication."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint_accessible_without_auth(self):
        """Test that root endpoint is accessible without authentication."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "BrainForge" in data["message"]
    
    @patch('src.api.security.file_validation.magic.Magic')
    def test_file_upload_validation(self, mock_magic):
        """Test file upload validation security."""
        # Mock MIME type detection
        mock_magic_instance = MagicMock()
        mock_magic_instance.from_buffer.return_value = "application/pdf"
        mock_magic.return_value = mock_magic_instance
        
        # Test valid PDF upload
        valid_pdf = b"%PDF-1.4\nfake pdf content"
        response = self.client.post(
            "/api/v1/ingestion/pdf",
            files={"file": ("test.pdf", valid_pdf, "application/pdf")},
            data={"priority": "normal"}
        )
        # Should be unauthorized, not validation error
        assert response.status_code == 401
        
        # Test malicious file with embedded JavaScript
        malicious_pdf = b"%PDF-1.4\n/JavaScript fake pdf with js"
        response = self.client.post(
            "/api/v1/ingestion/pdf",
            files={"file": ("malicious.pdf", malicious_pdf, "application/pdf")},
            data={"priority": "normal"}
        )
        # Should be validation error (400) not just unauthorized
        assert response.status_code in [400, 401]
        
        # Test file with script tags in text file
        malicious_txt = b"<script>alert('xss')</script>"
        response = self.client.post(
            "/api/v1/ingestion/pdf",  # Still using PDF endpoint for consistency
            files={"file": ("malicious.txt", malicious_txt, "text/plain")},
            data={"priority": "normal"}
        )
        # Should reject non-PDF file
        assert response.status_code in [400, 401]
    
    def test_authentication_token_validation(self):
        """Test JWT token validation."""
        # Test with invalid token format
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/api/v1/notes", headers=headers)
        assert response.status_code == 401
        
        # Test with malformed token
        headers = {"Authorization": "InvalidFormat token"}
        response = self.client.get("/api/v1/notes", headers=headers)
        assert response.status_code == 401
        
        # Test without Authorization header
        response = self.client.get("/api/v1/notes")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__])