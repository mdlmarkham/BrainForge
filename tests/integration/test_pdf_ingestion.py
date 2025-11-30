"""Integration tests for PDF ingestion workflow."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.models.ingestion import ProcessingState
from src.services.ingestion_service import IngestionService


class TestPDFIngestionIntegration:
    """Integration tests for PDF ingestion workflow."""

    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_pdf_file(self):
        """Create a mock PDF file for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            # Create a minimal PDF file
            temp_file.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n180\n%%EOF")
            temp_file_path = temp_file.name

        yield temp_file_path

        # Clean up
        Path(temp_file_path).unlink(missing_ok=True)

    @pytest.fixture
    def mock_ingestion_service(self):
        """Mock the ingestion service for testing."""
        with patch('src.api.routes.ingestion.ingestion_service') as mock_service:
            mock_service.create_ingestion_task = AsyncMock()
            mock_service.process_pdf_task = AsyncMock()
            mock_service.get_task_status = AsyncMock()

            # Mock successful task creation
            mock_task = MagicMock()
            mock_task.id = "test-task-id"
            mock_task.estimated_completion = "2025-01-01T00:00:00Z"
            mock_service.create_ingestion_task.return_value = mock_task

            # Mock successful processing
            mock_service.process_pdf_task.return_value = {
                "success": True,
                "task_id": "test-task-id",
                "quality_score": 0.8
            }

            # Mock status response
            mock_service.get_task_status.return_value = {
                "task_id": "test-task-id",
                "status": ProcessingState.INTEGRATED.value,
                "progress": 100,
                "estimated_completion": "2025-01-01T00:00:00Z"
            }

            yield mock_service

    def test_pdf_upload_success(self, client, mock_pdf_file, mock_ingestion_service):
        """Test successful PDF upload and processing."""
        with open(mock_pdf_file, "rb") as f:
            response = client.post(
                "/api/v1/ingestion/pdf",
                files={"file": ("test.pdf", f, "application/pdf")},
                data={
                    "source_url": "https://example.com/test.pdf",
                    "tags": "research,technical",
                    "priority": "normal"
                }
            )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert "task_id" in data
        assert "estimated_completion" in data

        # Verify service was called correctly
        mock_ingestion_service.create_ingestion_task.assert_called_once()
        mock_ingestion_service.process_pdf_task.assert_called_once()

    def test_pdf_upload_invalid_file_type(self, client):
        """Test PDF upload with invalid file type."""
        response = client.post(
            "/api/v1/ingestion/pdf",
            files={"file": ("test.txt", b"text content", "text/plain")},
            data={"priority": "normal"}
        )

        assert response.status_code == 400
        assert "File must be PDF" in response.json()["detail"]

    def test_pdf_upload_large_file(self, client, mock_pdf_file, mock_ingestion_service):
        """Test PDF upload with file size validation."""
        # Mock the file size to be larger than 100MB
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 200 * 1024 * 1024  # 200MB

            with open(mock_pdf_file, "rb") as f:
                response = client.post(
                    "/api/v1/ingestion/pdf",
                    files={"file": ("large.pdf", f, "application/pdf")},
                    data={"priority": "normal"}
                )

        assert response.status_code == 413
        assert "PDF file too large" in response.json()["detail"]

    def test_get_processing_status(self, client, mock_ingestion_service):
        """Test getting PDF processing status."""
        response = client.get("/api/v1/ingestion/pdf/test-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == ProcessingState.INTEGRATED.value
        assert data["progress"] == 100

        mock_ingestion_service.get_task_status.assert_called_once_with("test-task-id")

    def test_get_processing_status_not_found(self, client, mock_ingestion_service):
        """Test getting status for non-existent task."""
        mock_ingestion_service.get_task_status.return_value = {"error": "Task not found"}

        response = client.get("/api/v1/ingestion/pdf/nonexistent-task-id")

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_retry_pdf_processing(self, client):
        """Test retrying PDF processing."""
        response = client.post("/api/v1/ingestion/pdf/test-task-id/retry")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "retry_initiated"

    def test_batch_pdf_upload(self, client, mock_pdf_file, mock_ingestion_service):
        """Test batch PDF upload."""
        files = []
        for i in range(3):
            files.append(("files", open(mock_pdf_file, "rb"), "application/pdf"))

        try:
            response = client.post(
                "/api/v1/ingestion/pdf/batch",
                files=files,
                data={"batch_name": "test_batch"}
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_count"] == 3
            assert len(data["task_ids"]) == 3
            assert "batch_id" in data
            assert "estimated_completion" in data

        finally:
            # Close all file handles
            for file_tuple in files:
                file_tuple[1].close()

    def test_batch_pdf_upload_no_files(self, client):
        """Test batch PDF upload with no files."""
        response = client.post(
            "/api/v1/ingestion/pdf/batch",
            files=[],
            data={"batch_name": "test_batch"}
        )

        assert response.status_code == 400
        assert "No PDF files provided" in response.json()["detail"]

    def test_batch_pdf_upload_mixed_file_types(self, client, mock_pdf_file):
        """Test batch PDF upload with mixed file types."""
        files = [
            ("files", open(mock_pdf_file, "rb"), "application/pdf"),
            ("files", ("test.txt", b"text content", "text/plain"))
        ]

        try:
            response = client.post(
                "/api/v1/ingestion/pdf/batch",
                files=files,
                data={"batch_name": "test_batch"}
            )

            assert response.status_code == 400
            assert "is not a PDF" in response.json()["detail"]

        finally:
            # Close file handles
            files[0][1].close()

    @pytest.mark.asyncio
    async def test_ingestion_service_pdf_processing_flow(self, mock_pdf_file):
        """Test the complete PDF processing flow in ingestion service."""
        with patch('src.services.ingestion_service.PDFProcessor') as mock_pdf_processor:
            with patch('src.services.ingestion_service.AsyncSession') as mock_session:
                # Mock PDF processor
                mock_processor_instance = MagicMock()
                mock_processor_instance.validate_pdf = AsyncMock(return_value={"is_valid": True, "file_size": 1024})
                mock_processor_instance.process_pdf = AsyncMock(return_value={
                    "success": True,
                    "metadata": {
                        "page_count": 10,
                        "author": "Test Author",
                        "title": "Test Title",
                        "pdf_version": "1.4",
                        "encryption_status": "none",
                        "extraction_method": "dockling_advanced"
                    },
                    "text_result": {
                        "extracted_text": "Test extracted text content",
                        "quality_score": 0.8,
                        "character_count": 100,
                        "word_count": 20,
                        "processing_time_ms": 1000
                    }
                })
                mock_pdf_processor.return_value = mock_processor_instance

                # Mock database services
                mock_db_services = {}
                for service_name in ['ingestion_task_service', 'content_source_service',
                                   'pdf_metadata_service', 'pdf_processing_result_service',
                                   'processing_result_service', 'review_queue_service',
                                   'audit_trail_service', 'note_service']:
                    mock_service = MagicMock()
                    mock_service.create = AsyncMock()
                    mock_service.get = AsyncMock()
                    mock_service.update = AsyncMock()
                    mock_db_services[service_name] = mock_service

                # Mock the ingestion service
                ingestion_service = IngestionService("test_db_url")
                for service_name, mock_service in mock_db_services.items():
                    setattr(ingestion_service, service_name, mock_service)

                # Mock task retrieval
                mock_task = MagicMock()
                mock_task.id = "test-task-id"
                mock_task.source_url = "https://example.com/test.pdf"
                mock_db_services['ingestion_task_service'].get.return_value = mock_task

                # Test PDF processing
                result = await ingestion_service.process_pdf_task("test-task-id", mock_pdf_file)

                assert result["success"] is True
                assert result["quality_score"] == 0.8
                assert "content_source_id" in result
                assert "pdf_metadata_id" in result
                assert "processing_result_id" in result

                # Verify service calls
                mock_processor_instance.validate_pdf.assert_called_once_with(mock_pdf_file)
                mock_processor_instance.process_pdf.assert_called_once_with(mock_pdf_file)

    @pytest.mark.asyncio
    async def test_ingestion_service_validation_failure(self, mock_pdf_file):
        """Test PDF processing flow with validation failure."""
        with patch('src.services.ingestion_service.PDFProcessor') as mock_pdf_processor:
            with patch('src.services.ingestion_service.AsyncSession') as mock_session:
                # Mock PDF processor with validation failure
                mock_processor_instance = MagicMock()
                mock_processor_instance.validate_pdf = AsyncMock(return_value={
                    "is_valid": False,
                    "validation_notes": "Invalid PDF structure"
                })
                mock_pdf_processor.return_value = mock_processor_instance

                # Mock database services
                mock_db_services = {}
                for service_name in ['ingestion_task_service', 'audit_trail_service']:
                    mock_service = MagicMock()
                    mock_service.get = AsyncMock()
                    mock_service.update = AsyncMock()
                    mock_service.create = AsyncMock()
                    mock_db_services[service_name] = mock_service

                # Mock the ingestion service
                ingestion_service = IngestionService("test_db_url")
                for service_name, mock_service in mock_db_services.items():
                    setattr(ingestion_service, service_name, mock_service)

                # Mock task retrieval
                mock_task = MagicMock()
                mock_task.id = "test-task-id"
                mock_db_services['ingestion_task_service'].get.return_value = mock_task

                # Test PDF processing with validation failure
                result = await ingestion_service.process_pdf_task("test-task-id", mock_pdf_file)

                assert result["success"] is False
                assert "error" in result
                assert "PDF validation failed" in result["error"]

                # Verify task was marked as failed
                mock_db_services['ingestion_task_service'].update.assert_called()
                mock_db_services['audit_trail_service'].create.assert_called()
