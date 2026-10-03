# Implementation Guide

This guide walks through implementing the FastAPI backend architecture for the NDA Creator application.

## Project Structure Created

```
prelegal/
├── BACKEND_DESIGN.md                    # Complete architecture design
├── backend/
│   ├── main.py                          # FastAPI app (complete)
│   ├── requirements.txt                 # Dependencies (complete)
│   ├── .env.example                     # Configuration template (complete)
│   ├── README.md                        # Development guide (complete)
│   ├── QUICK_REFERENCE.md               # API reference (complete)
│   ├── IMPLEMENTATION_GUIDE.md           # This file
│   ├── test_api.py                      # Test script (complete)
│   │
│   ├── __init__.py                      # Package marker (complete)
│   │
│   ├── api/
│   │   ├── __init__.py                  # Package marker (complete)
│   │   └── routes.py                    # All endpoints (complete)
│   │
│   ├── schemas/
│   │   ├── __init__.py                  # Package marker (complete)
│   │   ├── documents.py                 # Request/response models (complete)
│   │   └── templates.py                 # Template metadata (complete)
│   │
│   ├── services/
│   │   ├── __init__.py                  # Package marker (complete)
│   │   ├── document_service.py          # Orchestration (complete)
│   │   ├── pdf_generator.py             # PDF generation (complete)
│   │   └── storage_service.py           # TODO: Cloud storage integration
│   │
│   └── utils/
│       ├── __init__.py                  # Package marker (complete)
│       ├── config.py                    # Configuration (complete)
│       ├── template_parser.py           # Template parsing (complete)
│       └── validators.py                # TODO: Advanced validation
│
└── templates/                           # Existing markdown templates
    ├── Mutual-NDA.md
    └── ... (other templates)
```

## Implementation Steps

### Phase 1: Setup & Core Infrastructure ✅ READY TO RUN

**Status:** All files created and ready to use

**Steps:**
1. Copy the `backend/` directory to your project
2. Create Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment file:
   ```bash
   cp .env.example .env
   ```

5. Start the server:
   ```bash
   python main.py
   ```

6. Verify it's working:
   ```bash
   # In another terminal
   python test_api.py
   ```

**What's Included:**
- ✅ FastAPI application entry point (main.py)
- ✅ Configuration management (utils/config.py)
- ✅ Pydantic data models (schemas/)
- ✅ Template parsing logic (utils/template_parser.py)
- ✅ PDF generation service (services/pdf_generator.py)
- ✅ Document orchestration service (services/document_service.py)
- ✅ Complete API endpoints (api/routes.py)
- ✅ Interactive API documentation (auto-generated at /docs)

### Phase 2: Frontend Integration (Next)

**Connect Frontend to Backend**

Create a frontend client to call the API:

```javascript
// Frontend example (React)
const generateDocument = async (template, fields) => {
  const response = await fetch('/api/documents/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template, fields })
  });
  
  const result = await response.json();
  
  // Download PDF
  window.location.href = result.download_url;
};
```

**Required Integration Points:**
1. Dynamic form generation from template schema
2. Form field validation
3. Document generation trigger
4. PDF download handling
5. Loading states and error handling

### Phase 3: Advanced Features (Later)

#### 3.1 Database Integration
```python
# Add to services/storage_service.py
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True)
    template_name = Column(String)
    created_at = Column(DateTime)
    user_id = Column(String)  # Future auth
```

#### 3.2 Async Document Generation
```python
# Use Celery + Redis for background tasks
from celery import Celery

celery_app = Celery('nda_creator', broker='redis://localhost')

@celery_app.task
def generate_document_async(template, fields):
    # Long-running task
    pass
```

#### 3.3 Authentication
```python
# Add to main.py
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/documents/generate")
async def generate_document(
    request: DocumentGenerateRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    # Verify API key
    pass
```

#### 3.4 E-Signature Integration
```python
# services/esignature_service.py
class DocuSignService:
    def send_for_signature(self, pdf_path, signer_emails):
        # Send to DocuSign or similar
        pass
```

### Phase 4: Production Deployment

**Docker Setup**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - RELOAD=false
      - LOG_LEVEL=INFO
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

**Environment Variables for Production**
```env
HOST=0.0.0.0
PORT=8000
RELOAD=False
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://yourdomain.com"]
```

## Testing

### Test the API

**Using test_api.py:**
```bash
python test_api.py
```

**Using curl:**
```bash
# List templates
curl http://localhost:8000/api/templates

# Get schema
curl http://localhost:8000/api/templates/Mutual-NDA/schema

# Generate document
curl -X POST http://localhost:8000/api/documents/generate \
  -H "Content-Type: application/json" \
  -d '{"template":"Mutual-NDA","fields":{...}}'

# Download
curl -O http://localhost:8000/api/documents/download/mutual_20240115_xyz789
```

**Using Swagger UI:**
1. Open http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters and execute

### Unit Tests (Future)

Create `backend/tests/`:
```bash
mkdir tests
touch tests/__init__.py
touch tests/test_template_parser.py
touch tests/test_pdf_generator.py
touch tests/test_routes.py
```

```python
# tests/test_template_parser.py
from utils.template_parser import TemplateParser

def test_extract_field_names():
    content = 'Text <span class="coverpage_link">Purpose</span> more'
    fields = TemplateParser.extract_field_names(content)
    assert "Purpose" in fields

def test_substitute_fields():
    template = '<span class="coverpage_link">Name</span>'
    result = TemplateParser.substitute_fields(template, {"Name": "John"})
    assert "John" in result
```

Run tests:
```bash
pytest tests/
pytest --cov=backend tests/  # With coverage
```

## Adding New Templates

1. **Create markdown template** in `templates/`:
   ```markdown
   # Agreement Title
   
   This is a clause mentioning <span class="coverpage_link">Field Name</span>.
   ```

2. **Add to catalog.json**:
   ```json
   {
     "name": "New-Agreement",
     "description": "Description here",
     "filename": "New-Agreement.md"
   }
   ```

3. **Add field definitions** in `backend/utils/template_parser.py`:
   ```python
   FIELD_DEFINITIONS = {
     "Field Name": FieldMetadata(
       name="Field Name",
       type=FieldType.TEXT,
       description="Description for users"
     ),
     # ... other fields
   }
   ```

4. **Test it**:
   ```bash
   curl http://localhost:8000/api/templates/New-Agreement/schema
   ```

## Extending the Architecture

### Add Custom PDF Styling

Edit `services/pdf_generator.py`:
```python
def _setup_custom_styles(self):
    self.styles.add(ParagraphStyle(
        name='MyStyle',
        fontSize=12,
        textColor='#FF0000',
        spaceAfter=12
    ))
```

### Add Field Validation

Create `backend/utils/validators.py`:
```python
def validate_date(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False

def validate_jurisdiction(value: str) -> bool:
    valid = ["California", "New York", "Delaware"]
    return value in valid
```

Use in `services/document_service.py`:
```python
from utils.validators import validate_date, validate_jurisdiction

# In generate_document():
for field_name, value in request.fields.items():
    if field_name == "Effective Date":
        if not validate_date(value):
            raise ValueError(f"Invalid date: {value}")
```

### Add Logging

```python
# In main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In routes.py
logger.info(f"Generating document: {request.template}")
logger.error(f"Generation failed: {error}")
```

## Performance Optimization

### 1. Cache Template Schemas
```python
from functools import lru_cache

@lru_cache(maxsize=32)
def get_template_schema(template_name: str):
    return TemplateParser.get_field_schema(template_name)
```

### 2. Async PDF Generation
```python
# Use aiofiles for async file I/O
import aiofiles

async def generate_pdf_async(content, output_path):
    async with aiofiles.open(output_path, 'wb') as f:
        await f.write(pdf_bytes)
```

### 3. Compress PDFs
```python
import PyPDF2

def compress_pdf(input_path, output_path):
    reader = PyPDF2.PdfReader(input_path)
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)
```

## Troubleshooting

### Port Already in Use
```bash
# Change port in .env
PORT=8001

# Or kill process on port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Template Not Found
```bash
# Check file exists
ls templates/Mutual-NDA.md

# Check catalog.json
cat catalog.json | grep "Mutual-NDA"
```

### PDF Generation Fails
```bash
# Check if ReportLab is installed
pip list | grep reportlab

# Test basic PDF generation
python -c "from reportlab.pdfgen import canvas; c = canvas.Canvas('test.pdf'); c.save()"
```

### CORS Issues (Frontend)
Update `.env`:
```env
CORS_ORIGINS=["http://localhost:3000","http://yourfrontend.com"]
```

## What's Working Now

✅ API endpoint structure  
✅ Pydantic validation  
✅ Template parsing with regex  
✅ PDF generation with ReportLab  
✅ Document service orchestration  
✅ Error handling  
✅ Interactive API documentation  
✅ Field auto-detection  
✅ Support for all 11 templates  

## Next Steps

1. **Run the server** - `python main.py`
2. **Test the API** - `python test_api.py`
3. **Check Swagger UI** - http://localhost:8000/docs
4. **Build frontend** - Create form generation logic
5. **Add authentication** - Secure API access
6. **Deploy** - Docker + cloud hosting

## Key Files to Modify

As you extend functionality:
- `backend/services/document_service.py` - Core logic
- `backend/utils/template_parser.py` - Template handling
- `backend/api/routes.py` - API endpoints
- `backend/schemas/documents.py` - Request/response types
- `backend/main.py` - App configuration

## Support

For questions or issues:
1. Check `backend/README.md` for setup help
2. Review `QUICK_REFERENCE.md` for API usage
3. Read `BACKEND_DESIGN.md` for architecture details
4. Run `test_api.py` to verify setup
5. Check Swagger UI at `/docs` for interactive testing

---

**Ready to start?** Run:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Then visit http://localhost:8000/docs to explore the API!
