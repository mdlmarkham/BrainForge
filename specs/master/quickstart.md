# Quickstart: PDF Processing for Ingestion Curation

**Feature**: Add PDF processing capability using dockling  
**Date**: 2025-11-29  
**Branch**: 002-ingestion-curation

## Overview

This guide provides step-by-step instructions for implementing PDF processing capabilities in the BrainForge ingestion pipeline using dockling for text extraction.

## Prerequisites

- Python 3.11+ environment
- Existing BrainForge installation
- PostgreSQL database with PGVector extension
- Docker (for containerized deployment)

## Installation

### 1. Add Dependencies

Add the following dependencies to `requirements.txt`:

```txt
dockling>=1.2.0
python-multipart>=0.0.6
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Implementation Steps

### Step 1: Create PDF Data Models

Create `src/models/pdf_metadata.py`:

```python
from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class PDFMetadata(Base):
    __tablename__ = "pdf_metadata"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    ingestion_task_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_tasks.id"), nullable=False)
    page_count = Column(Integer, nullable=False)
    author = Column(String, nullable=True)
    title = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    creation_date = Column(DateTime, nullable=True)
    modification_date = Column(DateTime, nullable=True)
    pdf_version = Column(String, nullable=False)
    encryption_status = Column(String, nullable=False)
    extraction_method = Column(String, nullable=False)
    extraction_quality_score = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### Step 2: Create PDF Processing Service

Create `src/services/pdf_processor.py`:

```python
import dockling
from typing import Optional, Dict, Any
from .base import BaseService

class PDFProcessor(BaseService):
    def __init__(self):
        self.parser = dockling.PDFParser()
    
    async def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF using dockling"""
        document = self.parser.parse(pdf_path)
        return {
            "page_count": document.page_count,
            "author": document.author,
            "title": document.title,
            "subject": document.subject,
            "creation_date": document.creation_date,
            "modification_date": document.modification_date,
            "pdf_version": document.pdf_version,
            "encryption_status": document.encryption_status
        }
    
    async def extract_text(self, pdf_path: str, method: str = "advanced") -> Dict[str, Any]:
        """Extract text from PDF with quality assessment"""
        document = self.parser.parse(pdf_path)
        
        if method == "basic":
            text = document.extract_text_basic()
        else:
            text = document.extract_text_advanced()
        
        quality_score = self._assess_text_quality(text)
        
        return {
            "extracted_text": text,
            "quality_score": quality_score,
            "method": method,
            "character_count": len(text),
            "word_count": len(text.split())
        }
    
    def _assess_text_quality(self, text: str) -> float:
        """Assess quality of extracted text (0.0-1.0)"""
        if not text or len(text.strip()) < 100:
            return 0.0
        
        # Basic quality assessment based on text characteristics
        lines = text.split('\n')
        avg_line_length = sum(len(line.strip()) for line in lines) / len(lines)
        
        # Higher score for longer average line length and fewer empty lines
        empty_lines = sum(1 for line in lines if not line.strip())
        quality = min(1.0, avg_line_length / 50) * (1 - empty_lines / len(lines))
        
        return max(0.0, min(1.0, quality))
```

### Step 3: Extend Ingestion Service

Update `src/services/ingestion.py` to include PDF processing:

```python
# Add PDF processing imports
from .pdf_processor import PDFProcessor

class IngestionService(BaseService):
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    async def process_pdf(self, file_path: str, task_id: UUID) -> Dict[str, Any]:
        """Process PDF file through full ingestion pipeline"""
        try:
            # Step 1: Extract metadata
            metadata = await self.pdf_processor.extract_metadata(file_path)
            
            # Step 2: Extract text with quality assessment
            text_result = await self.pdf_processor.extract_text(file_path)
            
            # Step 3: Generate summary and classifications
            summary = await self._generate_summary(text_result["extracted_text"])
            classifications = await self._classify_content(text_result["extracted_text"])
            
            return {
                "metadata": metadata,
                "text_result": text_result,
                "summary": summary,
                "classifications": classifications,
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### Step 4: Add API Routes

Update `src/api/routes/ingestion.py` to include PDF endpoints:

```python
from fastapi import UploadFile, File, Form
from typing import List, Optional

@router.post("/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    source_url: Optional[str] = Form(None),
    tags: Optional[List[str]] = Form([]),
    priority: str = Form("normal")
):
    """Submit PDF for ingestion processing"""
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(400, "File must be PDF")
    
    # Validate file size (100MB limit)
    if file.size > 100 * 1024 * 1024:
        raise HTTPException(413, "PDF file too large (>100MB)")
    
    # Create ingestion task
    task = await ingestion_service.create_pdf_task(
        file.filename, file.size, source_url, tags, priority
    )
    
    # Process asynchronously
    asyncio.create_task(ingestion_service.process_pdf_task(task.id))
    
    return {
        "task_id": task.id,
        "status": "accepted",
        "estimated_completion": datetime.now() + timedelta(minutes=2)
    }
```

### Step 5: Create Database Migration

Create migration for PDF metadata table:

```python
# alembic/versions/002_add_pdf_processing.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'pdf_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ingestion_task_id', sa.UUID(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('creation_date', sa.DateTime(), nullable=True),
        sa.Column('modification_date', sa.DateTime(), nullable=True),
        sa.Column('pdf_version', sa.String(), nullable=False),
        sa.Column('encryption_status', sa.String(), nullable=False),
        sa.Column('extraction_method', sa.String(), nullable=False),
        sa.Column('extraction_quality_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['ingestion_task_id'], ['ingestion_tasks.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add PDF content type to ingestion_tasks
    op.execute("ALTER TYPE content_type ADD VALUE 'pdf'")

def downgrade():
    op.drop_table('pdf_metadata')
```

## Testing

### Unit Tests

Create `tests/unit/test_pdf_processor.py`:

```python
import pytest
from src.services.pdf_processor import PDFProcessor

class TestPDFProcessor:
    @pytest.fixture
    def processor(self):
        return PDFProcessor()
    
    def test_text_quality_assessment(self, processor):
        # Test quality assessment with various text samples
        assert processor._assess_text_quality("") == 0.0
        assert processor._assess_text_quality("Short text") == 0.0
        assert processor._assess_text_quality("Valid text with reasonable length") > 0.5
```

### Integration Tests

Create `tests/integration/test_pdf_ingestion.py`:

```python
import pytest
from fastapi.testclient import TestClient

class TestPDFIngestion:
    def test_pdf_upload(self, client: TestClient):
        # Test PDF upload and processing
        with open("test.pdf", "rb") as f:
            response = client.post("/api/ingestion/pdf", files={"file": f})
            assert response.status_code == 202
            assert "task_id" in response.json()
```

## Deployment

### Docker Configuration

Update `Dockerfile` to include PDF processing dependencies:

```dockerfile
# Add PDF processing tools
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

### Environment Variables

Add PDF processing configuration to environment:

```bash
# config/database.env
PDF_PROCESSING_MAX_SIZE=100MB
PDF_PROCESSING_TIMEOUT=120
DOCKLING_CACHE_SIZE=1000
```

## Usage Examples

### Basic PDF Ingestion

```python
import requests

# Upload PDF for processing
files = {'file': open('research_paper.pdf', 'rb')}
data = {'tags': ['research', 'ai'], 'priority': 'high'}
response = requests.post('http://localhost:8000/api/ingestion/pdf', files=files, data=data)
task_id = response.json()['task_id']

# Check processing status
status = requests.get(f'http://localhost:8000/api/ingestion/pdf/{task_id}').json()
```

### Batch Processing

```python
# Upload multiple PDFs
files = [('files', open('doc1.pdf', 'rb')), ('files', open('doc2.pdf', 'rb'))]
data = {'batch_name': 'research_papers'}
response = requests.post('http://localhost:8000/api/ingestion/pdf/batch', files=files, data=data)
```

## Troubleshooting

### Common Issues

1. **PDF parsing fails**: Check if PDF is corrupted or password-protected
2. **Text extraction quality low**: Try advanced extraction method or manual review
3. **Processing timeout**: Reduce PDF size or increase timeout configuration
4. **Memory issues**: Monitor container memory usage and adjust limits

### Performance Optimization

- Use batch processing for multiple PDFs
- Implement caching for repeated PDF processing
- Monitor extraction quality scores for optimization
- Consider parallel processing for large PDF collections

## Next Steps

After implementation, proceed with:
1. Comprehensive testing with various PDF types
2. Performance benchmarking and optimization
3. Integration with existing review workflows
4. User acceptance testing and feedback collection