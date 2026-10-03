from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from backend.schemas.documents import DocumentGenerateRequest, DocumentGenerateResponse, ErrorResponse
from backend.schemas.templates import TemplateListItem, TemplateMetadata
from backend.services.document_service import DocumentService
from datetime import datetime
from typing import List


router = APIRouter(prefix="/api", tags=["documents"])
doc_service = DocumentService()


@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/info", tags=["info"])
async def api_info():
    """Get API information."""
    return {
        "name": "Prelegal NDA Generator API",
        "version": "1.0.0",
        "description": "API for generating legal documents from templates",
    }


@router.get("/templates", response_model=List[TemplateListItem], tags=["templates"])
async def list_templates():
    """List available templates."""
    try:
        templates = doc_service.get_available_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_name}/schema", tags=["templates"])
async def get_template_schema(template_name: str):
    """Get schema for a specific template."""
    try:
        metadata = doc_service.get_template_metadata(template_name)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/documents/generate",
    response_model=DocumentGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"]
)
async def generate_document(request: DocumentGenerateRequest):
    """Generate a document from a template."""
    try:
        doc_id, filename, download_url = doc_service.generate_document(
            request.template_name,
            request.fields
        )
        
        return DocumentGenerateResponse(
            document_id=doc_id,
            filename=filename,
            download_url=download_url,
            created_at=datetime.now(),
        )
    
    except ValueError as e:
        error_msg = str(e)
        missing_fields = None
        if "Missing required fields" in error_msg:
            missing_fields = error_msg.split(": ")[1].split(", ") if ": " in error_msg else []
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": error_msg,
                "missing_fields": missing_fields,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")


@router.get("/documents/download/{document_id}", tags=["documents"])
async def download_document(document_id: str):
    """Download a generated document."""
    try:
        pdf_path = doc_service.get_document_path(document_id)
        return FileResponse(
            path=pdf_path,
            filename=pdf_path.name,
            media_type="application/pdf",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
