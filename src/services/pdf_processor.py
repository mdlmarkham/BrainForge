"""PDF processing service for BrainForge ingestion pipeline using pdfplumber."""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from models.pdf_metadata import PDFMetadataCreate
from models.pdf_processing_result import PDFProcessingResultCreate

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF processing service using pdfplumber for text extraction and metadata collection."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize pdfplumber parser
        self.parser = None
        self._initialize_pdfplumber()
    
    def _initialize_pdfplumber(self):
        """Initialize pdfplumber PDF parser."""
        try:
            import pdfplumber
            self.parser = pdfplumber
            self.logger.info("PDFPlumber PDF parser initialized successfully")
        except ImportError:
            self.logger.warning("PDFPlumber not available - using fallback PDF processing")
            self.parser = None
    
    async def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF using pdfplumber or fallback method."""
        start_time = time.time()
        
        try:
            if self.parser:
                # Use pdfplumber for metadata extraction
                with self.parser.open(pdf_path) as pdf:
                    metadata = {
                        "page_count": len(pdf.pages),
                        "author": pdf.metadata.get('Author'),
                        "title": pdf.metadata.get('Title'),
                        "subject": pdf.metadata.get('Subject'),
                        "creation_date": pdf.metadata.get('CreationDate'),
                        "modification_date": pdf.metadata.get('ModDate'),
                        "pdf_version": "unknown",  # pdfplumber doesn't provide version
                        "encryption_status": "none" if not pdf.is_encrypted else "encrypted"
                    }
            else:
                # Fallback metadata extraction using basic file analysis
                metadata = await self._extract_metadata_fallback(pdf_path)
            
            processing_time = int((time.time() - start_time) * 1000)
            metadata["extraction_method"] = "pdfplumber" if self.parser else "fallback_basic"
            metadata["processing_time_ms"] = processing_time
            
            self.logger.info(f"PDF metadata extracted in {processing_time}ms: {pdf_path}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract PDF metadata: {e}")
            raise
    
    async def extract_text(self, pdf_path: str, method: str = "advanced") -> Dict[str, Any]:
        """Extract text from PDF with quality assessment."""
        start_time = time.time()
        
        try:
            extracted_text = ""
            quality_score = 0.0
            
            if self.parser:
                with self.parser.open(pdf_path) as pdf:
                    # Extract text from all pages
                    text_parts = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    
                    extracted_text = "\n".join(text_parts)
                    quality_score = self._assess_text_quality(extracted_text)
            else:
                # Fallback text extraction
                extracted_text, quality_score = await self._extract_text_fallback(pdf_path)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            result = {
                "extracted_text": extracted_text,
                "quality_score": quality_score,
                "method": method if self.parser else "fallback",
                "character_count": len(extracted_text),
                "word_count": len(extracted_text.split()),
                "processing_time_ms": processing_time,
                "pdfplumber_version": "0.10.3" if self.parser else "none"
            }
            
            self.logger.info(f"PDF text extracted in {processing_time}ms: {pdf_path} "
                           f"(quality: {quality_score:.2f}, chars: {len(extracted_text)})")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to extract PDF text: {e}")
            raise
    
    def _assess_text_quality(self, text: str) -> float:
        """Assess quality of extracted text (0.0-1.0)."""
        if not text or len(text.strip()) < 100:
            return 0.0
        
        # Basic quality assessment based on text characteristics
        lines = text.split('\n')
        avg_line_length = sum(len(line.strip()) for line in lines) / len(lines)
        
        # Higher score for longer average line length and fewer empty lines
        empty_lines = sum(1 for line in lines if not line.strip())
        quality = min(1.0, avg_line_length / 50) * (1 - empty_lines / len(lines))
        
        return max(0.0, min(1.0, quality))
    
    async def _extract_metadata_fallback(self, pdf_path: str) -> Dict[str, Any]:
        """Fallback metadata extraction when pdfplumber is not available."""
        path = Path(pdf_path)
        
        # Basic file-based metadata extraction
        return {
            "page_count": 0,  # Unknown without proper parser
            "author": None,
            "title": path.stem,  # Use filename as title
            "subject": None,
            "creation_date": None,
            "modification_date": path.stat().st_mtime if path.exists() else None,
            "pdf_version": "unknown",
            "encryption_status": "none"  # Assume no encryption
        }
    
    async def _extract_text_fallback(self, pdf_path: str) -> tuple[str, float]:
        """Fallback text extraction when pdfplumber is not available."""
        # This would typically use alternative PDF libraries like PyPDF2
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                extracted_text = "\n".join(text_parts)
                quality_score = self._assess_text_quality(extracted_text)
                return extracted_text, quality_score
        except ImportError:
            self.logger.warning(f"Using fallback text extraction for {pdf_path} - no text extracted")
            return "", 0.0
    
    async def validate_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Validate PDF file for processing."""
        path = Path(pdf_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {pdf_path}")
        
        file_size = path.stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError(f"PDF file too large: {file_size} bytes (>100MB)")
        
        # Basic file type validation
        if path.suffix.lower() != '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        return {
            "file_size": file_size,
            "file_name": path.name,
            "is_valid": True,
            "validation_notes": "PDF file validated successfully"
        }
    
    async def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF file through full extraction pipeline."""
        try:
            # Step 1: Validate PDF
            validation_result = await self.validate_pdf(pdf_path)
            
            # Step 2: Extract metadata
            metadata = await self.extract_metadata(pdf_path)
            
            # Step 3: Extract text
            text_result = await self.extract_text(pdf_path)
            
            return {
                "validation": validation_result,
                "metadata": metadata,
                "text_result": text_result,
                "success": True,
                "total_processing_time_ms": metadata.get("processing_time_ms", 0) + text_result.get("processing_time_ms", 0)
            }
            
        except Exception as e:
            self.logger.error(f"PDF processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "validation": {"is_valid": False},
                "metadata": {},
                "text_result": {}
            }