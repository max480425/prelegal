from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional


class DocumentGenerateRequest(BaseModel):
    """Request to generate a document."""
    template_name: str
    fields: Dict[str, str]


class DocumentGenerateResponse(BaseModel):
    """Response with generated document info."""
    document_id: str
    filename: str
    download_url: str
    created_at: datetime


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    missing_fields: Optional[list] = None
