# Prelegal Backend API

FastAPI backend for generating PDF documents from templates.

## Setup

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

**Interactive Docs:** `http://localhost:8000/docs`

### Environment Variables

Copy `.env.example` to `.env` and update as needed:

```bash
cp .env.example .env
```

## API Endpoints

- `POST /api/documents/generate` - Generate a PDF document
- `GET /api/templates` - List available templates
- `GET /api/templates/{template_name}/schema` - Get template field schema
- `GET /api/documents/download/{document_id}` - Download a generated document
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Example Request

```bash
curl -X POST http://localhost:8000/api/documents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "Mutual-NDA",
    "fields": {
      "Purpose": "Business evaluation",
      "Effective Date": "2024-01-15",
      "MNDA Term": "1 year",
      "Term of Confidentiality": "3 years after termination",
      "Governing Law": "California",
      "Jurisdiction": "California"
    }
  }'
```

## Development

The backend includes:
- Template parsing (auto-detects field placeholders)
- PDF generation using ReportLab
- Type-safe request/response models with Pydantic
- CORS support for frontend integration
- Comprehensive error handling
