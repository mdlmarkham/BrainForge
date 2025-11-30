"""Unit tests for PDF processor service."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Test cases for PDFProcessor service."""

    @pytest.fixture
    def pdf_processor(self):
        """Create a PDFProcessor instance for testing."""
        return PDFProcessor()

    @pytest.fixture
    def mock_pdf_path(self, tmp_path):
        """Create a mock PDF file path for testing."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%Mock PDF content")
        return str(pdf_file)

    def test_text_quality_assessment(self, pdf_processor):
        """Test text quality assessment with various text samples."""
        # Test empty text
        assert pdf_processor._assess_text_quality("") == 0.0

        # Test short text
        assert pdf_processor._assess_text_quality("Short text") == 0.0

        # Test valid text with reasonable length
        valid_text = "This is a valid text sample with reasonable length for quality assessment."
        quality_score = pdf_processor._assess_text_quality(valid_text)
        assert 0.5 < quality_score < 1.0

        # Test text with many empty lines
        text_with_empty_lines = "Line 1\n\n\nLine 2\n\n\nLine 3"
        quality_score = pdf_processor._assess_text_quality(text_with_empty_lines)
        assert 0.0 < quality_score < 0.5

    @pytest.mark.asyncio
    async def test_validate_pdf_success(self, pdf_processor, mock_pdf_path):
        """Test PDF validation with valid file."""
        result = await pdf_processor.validate_pdf(mock_pdf_path)

        assert result["is_valid"] is True
        assert result["file_size"] > 0
        assert result["file_name"] == "test.pdf"
        assert "validation_notes" in result

    @pytest.mark.asyncio
    async def test_validate_pdf_file_not_found(self, pdf_processor):
        """Test PDF validation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            await pdf_processor.validate_pdf("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_validate_pdf_invalid_type(self, pdf_processor, tmp_path):
        """Test PDF validation with non-PDF file."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("This is a text file, not a PDF")

        with pytest.raises(ValueError, match="File is not a PDF"):
            await pdf_processor.validate_pdf(str(text_file))

    @pytest.mark.asyncio
    async def test_extract_metadata_fallback(self, pdf_processor, mock_pdf_path):
        """Test metadata extraction with fallback method."""
        # Mock dockling to be unavailable
        with patch.object(pdf_processor, 'parser', None):
            result = await pdf_processor.extract_metadata(mock_pdf_path)

            assert "extraction_method" in result
            assert result["extraction_method"] == "fallback_basic"
            assert "processing_time_ms" in result
            assert result["processing_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_extract_text_fallback(self, pdf_processor, mock_pdf_path):
        """Test text extraction with fallback method."""
        # Mock dockling to be unavailable
        with patch.object(pdf_processor, 'parser', None):
            result = await pdf_processor.extract_text(mock_pdf_path)

            assert "extracted_text" in result
            assert "quality_score" in result
            assert result["quality_score"] == 0.0  # Fallback returns empty text
            assert "method" in result
            assert result["method"] == "fallback"
            assert "processing_time_ms" in result
            assert result["processing_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_process_pdf_success(self, pdf_processor, mock_pdf_path):
        """Test full PDF processing pipeline."""
        result = await pdf_processor.process_pdf(mock_pdf_path)

        assert "success" in result
        assert "validation" in result
        assert "metadata" in result
        assert "text_result" in result
        assert "total_processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_process_pdf_failure(self, pdf_processor):
        """Test PDF processing with invalid file."""
        result = await pdf_processor.process_pdf("/invalid/path.pdf")

        assert result["success"] is False
        assert "error" in result
        assert result["validation"]["is_valid"] is False

    def test_quality_score_calculation(self, pdf_processor):
        """Test quality score calculation with various text inputs."""
        # Test with very short text
        short_text = "a" * 50  # Less than 100 characters
        score = pdf_processor._assess_text_quality(short_text)
        assert score == 0.0

        # Test with reasonable text
        reasonable_text = "This is a reasonable length text with proper content for testing quality assessment."
        score = pdf_processor._assess_text_quality(reasonable_text)
        assert 0.0 < score <= 1.0

        # Test with text containing many empty lines
        empty_line_text = "Line 1\n\n\n\n\nLine 2"  # Many empty lines
        score = pdf_processor._assess_text_quality(empty_line_text)
        assert 0.0 < score < 0.5  # Should be penalized for empty lines

    @pytest.mark.asyncio
    async def test_extract_metadata_with_dockling_mock(self, pdf_processor, mock_pdf_path):
        """Test metadata extraction with mocked dockling."""
        # Create a mock dockling document
        mock_document = MagicMock()
        mock_document.page_count = 10
        mock_document.author = "Test Author"
        mock_document.title = "Test Title"
        mock_document.subject = "Test Subject"
        mock_document.creation_date = "2025-01-01"
        mock_document.modification_date = "2025-01-02"
        mock_document.pdf_version = "1.4"
        mock_document.encryption_status = "none"

        # Mock the parser and its parse method
        mock_parser = MagicMock()
        mock_parser.parse.return_value = mock_document
        pdf_processor.parser = mock_parser

        result = await pdf_processor.extract_metadata(mock_pdf_path)

        assert result["page_count"] == 10
        assert result["author"] == "Test Author"
        assert result["title"] == "Test Title"
        assert result["extraction_method"] == "dockling_advanced"
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_extract_text_with_dockling_mock(self, pdf_processor, mock_pdf_path):
        """Test text extraction with mocked dockling."""
        # Create a mock dockling document
        mock_document = MagicMock()
        mock_document.extract_text_basic.return_value = "Basic extracted text"
        mock_document.extract_text_advanced.return_value = "Advanced extracted text"

        # Mock the parser and its parse method
        mock_parser = MagicMock()
        mock_parser.parse.return_value = mock_document
        pdf_processor.parser = mock_parser

        # Test basic extraction
        result_basic = await pdf_processor.extract_text(mock_pdf_path, method="basic")
        assert result_basic["extracted_text"] == "Basic extracted text"
        assert result_basic["method"] == "basic"

        # Test advanced extraction
        result_advanced = await pdf_processor.extract_text(mock_pdf_path, method="advanced")
        assert result_advanced["extracted_text"] == "Advanced extracted text"
        assert result_advanced["method"] == "advanced"
