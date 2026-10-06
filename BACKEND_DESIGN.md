# FastAPI Backend Architecture - NDA Creator

## Overview
Minimal, elegant design for generating customized legal documents (PDFs) from markdown templates with coverpage field substitution. Extensible to support all templates in the catalog.

---

## 1. API Endpoint Structure

### Primary Endpoint
```
POST /api/documents/generate
Content-Type: application/json

Request Body:
{
  "template": "Mutual-NDA",
  "fields": {
    "Purpose": "Evaluation of partnership opportunity",
    "Effective Date": "January 1, 2024",
    "MNDA Term": "2 years",
    "Term of Confidentiality": "3 years",
    "Governing Law": "California",
    "Jurisdiction": "Northern District of California",
    "Party A Name": "Acme Corp",
    "Party A Address": "123 Main St, San Francisco, CA 94102",
    "Party B Name": "Tech Startup Inc",
    "Party B Address": "456 Oak Ave, Palo Alto, CA 94301"
  }
}

Response:
{
  "document_id": "mnda_20240101_abc123",
  "filename": "Mutual-NDA-20240101.pdf",
  "download_url": "/api/documents/download/mnda_20240101_abc123"
}
```

### Secondary Endpoints
```
GET /api/templates
→ Returns list of available templates with required fields metadata

GET /api/templates/{template_name}/schema
→ Returns JSON schema of required and optional fields for a specific template

GET /api/documents/download/{document_id}
→ Returns PDF file for download

GET /api/documents/{document_id}/metadata
→ Returns document metadata (creation date, template used, etc.)
```

---

## 2. Data Models (Pydantic)

### Core Models

```python
# schemas/templates.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class FieldType(str, Enum):
    TEXT = "text"
    DATE = "date"
    MULTILINE = "multiline"
    DROPDOWN = "dropdown"

class FieldMetadata(BaseModel):
    """Metadata for a coverpage field"""
    name: str
    type: FieldType = FieldType.TEXT
    required: bool = True
    pattern: Optional[str] = None  # Regex for validation
    description: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None  # For dropdown fields

class TemplateMetadata(BaseModel):
    """Template information and field requirements"""
    name: str
    description: str
    filename: str
    version: str = "1.0"
    fields: List[FieldMetadata]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mutual-NDA",
                "description": "Mutual Non-Disclosure Agreement",
                "filename": "Mutual-NDA.md",
                "fields": [
                    {
                        "name": "Purpose",
                        "type": "text",
                        "required": True,
                        "placeholder": "e.g., Evaluation of partnership"
                    },
                    {
                        "name": "Effective Date",
                        "type": "date",
                        "required": True
                    }
                ]
            }
        }

# schemas/documents.py
class DocumentGenerateRequest(BaseModel):
    """Request to generate a new document"""
    template: str  # Template name (e.g., "Mutual-NDA")
    fields: Dict[str, str]  # Field name → value mappings
    
    class Config:
        json_schema_extra = {
            "example": {
                "template": "Mutual-NDA",
                "fields": {
                    "Purpose": "Evaluation of partnership",
                    "Effective Date": "2024-01-01",
                    "MNDA Term": "2 years",
                    "Term of Confidentiality": "3 years",
                    "Governing Law": "California",
                    "Jurisdiction": "Northern District of California",
                    "Party A Name": "Acme Corp",
                    "Party B Name": "Tech Startup Inc"
                }
            }
        }

class DocumentGenerateResponse(BaseModel):
    """Response after document generation"""
    document_id: str
    filename: str
    download_url: str
    created_at: str  # ISO 8601 timestamp

class DocumentMetadata(BaseModel):
    """Metadata about a generated document"""
    document_id: str
    template_name: str
    filename: str
    created_at: str
    status: str  # "generated", "archived", etc.
    file_size_bytes: int
```

---

## 3. Template Parsing Strategy

### Regex-Based Field Detection

```python
# utils/template_parser.py
import re
from typing import Set, List

class TemplateParser:
    """Parse markdown templates and extract coverpage_link fields"""
    
    # Regex pattern to match: <span class="coverpage_link">Field Name</span>
    COVERPAGE_PATTERN = r'<span class="coverpage_link">([^<]+)</span>'
    
    @staticmethod
    def extract_field_names(template_content: str) -> Set[str]:
        """
        Extract all unique field names from markdown template.
        
        Returns:
            Set of field names, e.g., {"Purpose", "Effective Date", "Governing Law"}
        """
        matches = re.findall(TemplateParser.COVERPAGE_PATTERN, template_content)
        return set(matches)
    
    @staticmethod
    def substitute_fields(template_content: str, field_values: Dict[str, str]) -> str:
        """
        Replace all coverpage_link spans with provided values.
        
        Args:
            template_content: Raw markdown template
            field_values: Dict mapping field names to values
            
        Returns:
            Modified markdown with substitutions
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = TemplateParser.extract_field_names(template_content)
        provided_fields = set(field_values.keys())
        
        missing = required_fields - provided_fields
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        result = template_content
        for field_name, value in field_values.items():
            pattern = f'<span class="coverpage_link">{field_name}</span>'
            result = result.replace(pattern, value)
        
        return result
    
    @staticmethod
    def get_field_schema(template_name: str) -> TemplateMetadata:
        """
        Auto-detect fields from template and generate metadata schema.
        Includes predefined field type hints and validation rules.
        """
        # Load template file
        template_path = f"templates/{template_name}.md"
        with open(template_path, 'r') as f:
            content = f.read()
        
        field_names = TemplateParser.extract_field_names(content)
        
        # Predefined field schemas (extensible)
        field_definitions = {
            "Purpose": FieldMetadata(
                name="Purpose",
                type=FieldType.MULTILINE,
                description="What is this agreement for?",
                placeholder="e.g., Evaluation of potential partnership"
            ),
            "Effective Date": FieldMetadata(
                name="Effective Date",
                type=FieldType.DATE,
                description="Date agreement becomes effective"
            ),
            "MNDA Term": FieldMetadata(
                name="MNDA Term",
                type=FieldType.TEXT,
                description="Duration of agreement (e.g., '2 years')",
                placeholder="e.g., 2 years"
            ),
            "Term of Confidentiality": FieldMetadata(
                name="Term of Confidentiality",
                type=FieldType.TEXT,
                description="How long confidentiality obligations last",
                placeholder="e.g., 3 years from disclosure"
            ),
            "Governing Law": FieldMetadata(
                name="Governing Law",
                type=FieldType.TEXT,
                options=["California", "New York", "Delaware", "Texas", "Other"],
                description="Which state's laws govern this agreement?"
            ),
            "Jurisdiction": FieldMetadata(
                name="Jurisdiction",
                type=FieldType.TEXT,
                description="Where disputes will be resolved",
                placeholder="e.g., Northern District of California"
            ),
            "Party A Name": FieldMetadata(
                name="Party A Name",
                type=FieldType.TEXT,
                description="Name of first party"
            ),
            "Party A Address": FieldMetadata(
                name="Party A Address",
                type=FieldType.MULTILINE,
                description="Address of first party"
            ),
            "Party B Name": FieldMetadata(
                name="Party B Name",
                type=FieldType.TEXT,
                description="Name of second party"
            ),
            "Party B Address": FieldMetadata(
                name="Party B Address",
                type=FieldType.MULTILINE,
                description="Address of second party"
            ),
        }
        
        # Build schema for detected fields
        fields = [
            field_definitions.get(fname, FieldMetadata(name=fname))
            for fname in sorted(field_names)
        ]
        
        return TemplateMetadata(
            name=template_name,
            description=f"{template_name} template",
            filename=f"{template_name}.md",
            fields=fields
        )
```

---

## 4. PDF Generation Approach

### Using ReportLab (Recommended)

```python
# services/pdf_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from io import BytesIO
import markdown
import re
from datetime import datetime

class PDFGenerator:
    """Generate PDF documents from processed markdown templates"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure custom styles for legal documents"""
        # Body text - justified, 11pt
        self.styles.add(ParagraphStyle(
            name='LegalBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        ))
        
        # Heading for numbered sections
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor='#000000',
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Title
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor='#000000',
            alignment=TA_LEFT,
            spaceAfter=20,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
    
    def generate_pdf(
        self,
        markdown_content: str,
        document_id: str,
        output_path: str
    ) -> bytes:
        """
        Convert processed markdown to PDF.
        
        Args:
            markdown_content: Markdown text with all fields substituted
            document_id: Unique document identifier
            output_path: Where to save the PDF
            
        Returns:
            PDF file as bytes
        """
        # Convert markdown to HTML for better formatting control
        html_content = markdown.markdown(markdown_content)
        
        # Create PDF document in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        
        # Build story (list of flowable elements)
        story = []
        
        # Parse HTML and convert to Platypus elements
        story.extend(self._html_to_elements(html_content))
        
        # Add footer with document ID
        story.append(Spacer(1, 0.3*inch))
        footer = Paragraph(
            f"<font size=8 color='#999999'>Generated: {datetime.now().isoformat()} | ID: {document_id}</font>",
            self.styles['Normal']
        )
        story.append(footer)
        
        # Build and save PDF
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        
        # Save to file system
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        return pdf_bytes
    
    def _html_to_elements(self, html_content: str) -> list:
        """Convert HTML to ReportLab Platypus elements"""
        elements = []
        
        # Simple parsing: split by tags and create paragraphs
        # In production, consider using html2text or similar
        lines = html_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                elements.append(Spacer(1, 0.1*inch))
                continue
            
            if line.startswith('<h1>'):
                text = re.sub(r'<h1>(.*?)</h1>', r'\1', line)
                elements.append(Paragraph(text, self.styles['DocumentTitle']))
            elif line.startswith('<h2>'):
                text = re.sub(r'<h2>(.*?)</h2>', r'\1', line)
                elements.append(Paragraph(text, self.styles['SectionHeading']))
            elif line.startswith('<p>'):
                text = re.sub(r'<p>(.*?)</p>', r'\1', line)
                text = self._sanitize_html(text)
                elements.append(Paragraph(text, self.styles['LegalBody']))
        
        return elements
    
    def _sanitize_html(self, text: str) -> str:
        """Remove remaining HTML tags and convert entities"""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&quot;', '"')
        text = text.replace('&amp;', '&')
        return text
```

### Alternative: Python-DOCX → PDF Conversion

For complex formatting requirements, use python-docx + pandoc:

```python
# Alternative approach (if needed)
# Install: pip install python-docx pandoc
import subprocess
from docx import Document

class DOCXGenerator:
    """Generate DOCX, then convert to PDF"""
    
    def generate(self, markdown_content: str, output_path: str):
        # Create DOCX
        doc = Document()
        doc.add_paragraph(markdown_content)
        docx_path = output_path.replace('.pdf', '.docx')
        doc.save(docx_path)
        
        # Convert to PDF with pandoc
        subprocess.run(['pandoc', docx_path, '-o', output_path])
```

---

## 5. File Structure & Key Files

```
prelegal/
├── backend/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entry point
│   ├── requirements.txt                 # Python dependencies
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                    # All endpoints (POST /generate, GET /templates, etc.)
│   │   └── health.py                    # Health check endpoint
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── documents.py                 # DocumentGenerateRequest, Response
│   │   └── templates.py                 # TemplateMetadata, FieldMetadata
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py          # Orchestrates generation (template → PDF)
│   │   ├── pdf_generator.py             # ReportLab PDF generation
│   │   └── storage_service.py           # Save/retrieve PDFs from filesystem
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── template_parser.py           # Regex-based field extraction
│   │   ├── validators.py                # Field validation
│   │   └── config.py                    # Configuration (paths, settings)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── document.py                  # Database model (optional, for metadata)
│   │
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py             # Global error handling
│
├── templates/                           # Existing markdown templates
│   ├── Mutual-NDA.md
│   ├── Data-Processing-Agreement.md
│   └── ...
│
├── .env                                 # Environment variables
└── docker-compose.yml                   # Optional: Local dev container
```

---

## 6. Implementation Sequence

### Phase 1: Core Infrastructure
1. Set up FastAPI app with proper structure
2. Implement TemplateParser with regex field detection
3. Create Pydantic schemas (templates, documents)
4. Build DocumentService orchestration layer

### Phase 2: PDF Generation
1. Implement PDFGenerator with ReportLab
2. Test markdown → PDF conversion
3. Add custom styles for legal documents

### Phase 3: API Endpoints
1. `POST /api/documents/generate` - Main endpoint
2. `GET /api/templates` - List templates
3. `GET /api/templates/{name}/schema` - Get field schema
4. `GET /api/documents/download/{id}` - Download PDF

### Phase 4: Storage & Metadata
1. File storage service (local disk or cloud)
2. Document metadata tracking
3. Cleanup/archival policies

### Phase 5: Advanced Features
1. Field validation and error handling
2. Concurrent document generation
3. API rate limiting and auth
4. Signature integration

---

## 7. Technology Stack

### Core
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation and schema
- **ReportLab** - PDF generation
- **Markdown** - Template processing
- **Python 3.10+**

### Optional
- **Pandoc** - Advanced document conversion
- **SQLAlchemy** - If adding database persistence
- **Redis** - For async job queue (background generation)
- **Docker** - Containerization

### Dependencies
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
reportlab==4.0.7
markdown==3.5.1
python-multipart==0.0.6
aiofiles==23.2.1
```

---

## 8. Key Design Principles

1. **Separation of Concerns**
   - TemplateParser: Markdown manipulation
   - PDFGenerator: PDF creation
   - DocumentService: Orchestration
   - Storage: File I/O

2. **Extensibility**
   - Field metadata defined in `field_definitions` dict
   - Easy to add new templates without code changes
   - Support different PDF generators via interface

3. **Type Safety**
   - Pydantic models for all I/O
   - Clear validation rules
   - IDE autocomplete support

4. **Testability**
   - Each service is independently testable
   - Mock-friendly architecture
   - No hard dependencies on external systems

5. **Minimal Dependencies**
   - ReportLab for PDF (pure Python, no native bindings)
   - Markdown library (standard)
   - FastAPI (async, modern)

---

## 9. Error Handling Strategy

```python
# Example error responses
class TemplateNotFoundError(Exception):
    """Raised when template doesn't exist"""
    pass

class MissingFieldError(Exception):
    """Raised when required field is missing"""
    pass

class InvalidFieldValueError(Exception):
    """Raised when field value fails validation"""
    pass

# API error responses
HTTP 404: {"error": "template_not_found", "detail": "Mutual-NDA template not found"}
HTTP 400: {"error": "missing_fields", "detail": "Missing fields: [Purpose, Effective Date]"}
HTTP 400: {"error": "validation_error", "detail": "Effective Date must be valid ISO date"}
HTTP 500: {"error": "generation_failed", "detail": "PDF generation failed"}
```

---

## 10. Example Request/Response Flow

```python
# Request
POST /api/documents/generate
{
  "template": "Mutual-NDA",
  "fields": {
    "Purpose": "Evaluation of AI partnership",
    "Effective Date": "2024-01-15",
    "MNDA Term": "2 years",
    "Term of Confidentiality": "3 years",
    "Governing Law": "California",
    "Jurisdiction": "Northern District of California",
    "Party A Name": "TechCorp Inc",
    "Party B Name": "AILabs LLC"
  }
}

# Processing
1. Validate template exists → Load Mutual-NDA.md
2. Validate all required fields present
3. Parse template to find coverpage_link fields
4. Substitute field values in markdown
5. Convert markdown to PDF via ReportLab
6. Save PDF to disk with unique ID
7. Record metadata (creation time, template, filename)

# Response
HTTP 200
{
  "document_id": "mnda_20240115_xyz789",
  "filename": "Mutual-NDA-20240115.pdf",
  "download_url": "/api/documents/download/mnda_20240115_xyz789",
  "created_at": "2024-01-15T10:30:45.123456Z"
}

# Subsequent download
GET /api/documents/download/mnda_20240115_xyz789
→ Returns PDF file (application/pdf)
```

---

## 11. Future Enhancements

- **E-signature Integration**: DocuSign, HelloSign
- **Multi-language Support**: Template translation
- **Version Control**: Track template changes
- **Collaborative Editing**: Real-time field editing
- **Workflow**: Automate party notifications, signature requests
- **Analytics**: Usage tracking, field statistics
- **Approval Flow**: Template review and approval before generation
- **Audit Trail**: Log all generation requests

---

## Summary

This architecture provides:
✅ Clean separation of concerns  
✅ Type-safe request/response handling  
✅ Extensible template system  
✅ Minimal but powerful PDF generation  
✅ Easy to test and maintain  
✅ Ready for feature expansion  

Start with Phase 1-3 for MVP, then add persistence and advanced features as needed.
