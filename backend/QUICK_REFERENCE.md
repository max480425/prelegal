# API Quick Reference

## Base URL
```
http://localhost:8000/api
```

## Endpoints

### 1. List All Templates
```bash
GET /templates
```

**Response:**
```json
[
  {
    "name": "Mutual-NDA",
    "description": "Mutual Non-Disclosure Agreement",
    "filename": "Mutual-NDA.md"
  },
  ...
]
```

---

### 2. Get Template Field Schema
```bash
GET /templates/{template_name}/schema
```

**Example:**
```bash
curl http://localhost:8000/api/templates/Mutual-NDA/schema
```

**Response:**
```json
{
  "name": "Mutual-NDA",
  "description": "Mutual Non-Disclosure Agreement",
  "filename": "Mutual-NDA.md",
  "version": "1.0",
  "fields": [
    {
      "name": "Effective Date",
      "type": "date",
      "required": true,
      "description": "Date agreement becomes effective"
    },
    {
      "name": "Governing Law",
      "type": "dropdown",
      "required": true,
      "description": "Which state's laws govern this agreement?",
      "options": ["California", "New York", "Delaware", "Texas", "Other"]
    },
    ...
  ]
}
```

---

### 3. Generate a Document
```bash
POST /documents/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "template": "Mutual-NDA",
  "fields": {
    "Purpose": "Evaluation of AI partnership opportunity",
    "Effective Date": "2024-01-15",
    "MNDA Term": "2 years",
    "Term of Confidentiality": "3 years from disclosure",
    "Governing Law": "California",
    "Jurisdiction": "Northern District of California",
    "Party A Name": "TechCorp Inc",
    "Party A Address": "123 Main St, San Francisco, CA 94102",
    "Party B Name": "AI Labs LLC",
    "Party B Address": "456 Oak Ave, Palo Alto, CA 94301"
  }
}
```

**Response (HTTP 201):**
```json
{
  "document_id": "mutual_20240115_xyz789",
  "filename": "Mutual-NDA-20240115.pdf",
  "download_url": "/api/documents/download/mutual_20240115_xyz789",
  "created_at": "2024-01-15T10:30:45.123456Z"
}
```

---

### 4. Download a Document
```bash
GET /documents/download/{document_id}
```

**Example:**
```bash
curl -O http://localhost:8000/api/documents/download/mutual_20240115_xyz789
```

Returns the PDF file with `Content-Type: application/pdf`

---

### 5. Get API Info
```bash
GET /info
```

**Response:**
```json
{
  "name": "NDA Creator API",
  "version": "0.1.0",
  "description": "Backend for generating customized legal documents",
  "template_count": 11,
  "templates": ["Mutual-NDA", "Data-Processing-Agreement", ...]
}
```

---

### 6. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "NDA Creator API",
  "version": "0.1.0"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "detail": "Detailed error message"
}
```

### Common Errors

**Missing Template (HTTP 404):**
```json
{
  "error": "template_not_found",
  "detail": "Template not found: InvalidTemplate"
}
```

**Missing Required Fields (HTTP 400):**
```json
{
  "error": "missing_fields",
  "detail": "Missing required fields: Purpose, Effective Date"
}
```

**PDF Generation Failed (HTTP 500):**
```json
{
  "error": "generation_failed",
  "detail": "Document generation failed"
}
```

---

## cURL Examples

### List templates:
```bash
curl http://localhost:8000/api/templates
```

### Get Mutual-NDA schema:
```bash
curl http://localhost:8000/api/templates/Mutual-NDA/schema
```

### Generate document:
```bash
curl -X POST http://localhost:8000/api/documents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template": "Mutual-NDA",
    "fields": {
      "Purpose": "Partnership evaluation",
      "Effective Date": "2024-01-15",
      "MNDA Term": "2 years",
      "Term of Confidentiality": "3 years",
      "Governing Law": "California",
      "Jurisdiction": "Northern District of California",
      "Party A Name": "Company A",
      "Party B Name": "Company B"
    }
  }'
```

### Download document:
```bash
curl -O http://localhost:8000/api/documents/download/mutual_20240115_xyz789
```

---

## Mutual-NDA Template Fields

When generating a Mutual-NDA, these fields are required:

| Field | Type | Example |
|-------|------|---------|
| Purpose | multiline | "Evaluation of potential partnership" |
| Effective Date | date | "2024-01-15" |
| MNDA Term | text | "2 years" |
| Term of Confidentiality | text | "3 years from disclosure" |
| Governing Law | dropdown | "California" |
| Jurisdiction | text | "Northern District of California" |
| Party A Name | text | "Acme Corp" |
| Party A Address | multiline | "123 Main St, San Francisco, CA" |
| Party B Name | text | "Tech Startup Inc" |
| Party B Address | multiline | "456 Oak Ave, Palo Alto, CA" |

---

## Field Types

- **text** - Single-line text input (name, jurisdiction, etc.)
- **date** - Date picker (ISO 8601 format: YYYY-MM-DD)
- **multiline** - Multi-line text area (addresses, descriptions)
- **dropdown** - Select from predefined options
- **email** - Email address validation

---

## Development Notes

### Interactive API Documentation
When the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API exploration where you can test endpoints directly.

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET) |
| 201 | Created (POST document generation) |
| 400 | Bad Request (validation error) |
| 404 | Not Found (template/document doesn't exist) |
| 500 | Server Error (PDF generation failure) |

---

## Rate Limiting (Future)

Once implemented, rate limits will be enforced per IP or API key.
Check response headers for rate limit info.

---

## Authentication (Future)

Currently, no authentication is required. In production:
- API key authentication will be added
- Endpoints will require `Authorization: Bearer {api_key}` header

---

## Pagination (Future)

For list endpoints, pagination may be added:
- `?page=1&page_size=10`
- Response will include `total_count`, `has_next`, `has_previous`
