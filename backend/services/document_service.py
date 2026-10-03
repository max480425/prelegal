import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
from backend.utils.template_parser import TemplateParser
from backend.utils.config import get_settings
from backend.services.pdf_generator import PDFGenerator


class DocumentService:
    """Service for document generation and management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.templates_dir = self.settings.templates_path
        self.documents_dir = self.settings.documents_path
    
    def get_available_templates(self) -> list:
        """Get list of available templates."""
        try:
            catalog_path = Path(__file__).parent.parent.parent / "catalog.json"
            if not catalog_path.exists():
                return []
            
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
            return catalog
        except Exception:
            return []
    
    def get_template_metadata(self, template_name: str) -> Dict:
        """Get metadata for a template."""
        # Try common variations
        possible_names = [
            f"{template_name}.md",
            template_name if template_name.endswith('.md') else f"{template_name}.md"
        ]
        
        for name in possible_names:
            template_path = self.templates_dir / name
            if template_path.exists():
                content = TemplateParser.load_template(template_path)
                fields = TemplateParser.extract_fields(content)
                schema = {}
                for field in fields:
                    schema[field] = TemplateParser.get_field_schema(field)
                
                return {
                    "name": template_name,
                    "filename": name,
                    "fields": schema,
                }
        
        raise ValueError(f"Template not found: {template_name}")
    
    def generate_document(self, template_name: str, fields: Dict[str, str]) -> Tuple[str, str, str]:
        """
        Generate a document from template.
        
        Returns:
            Tuple of (document_id, filename, download_url)
        """
        # Find template
        possible_names = [
            f"{template_name}.md",
            template_name if template_name.endswith('.md') else f"{template_name}.md"
        ]
        
        template_path = None
        for name in possible_names:
            path = self.templates_dir / name
            if path.exists():
                template_path = path
                break
        
        if not template_path:
            raise ValueError(f"Template not found: {template_name}")
        
        # Load template
        content = TemplateParser.load_template(template_path)
        
        # Validate fields
        is_valid, missing_fields = TemplateParser.validate_fields(content, fields)
        if not is_valid:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Substitute fields
        substituted = TemplateParser.substitute_fields(content, fields)
        
        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_id = f"{template_name.lower().replace(' ', '_')}_{timestamp}"
        filename = f"{template_name.replace(' ', '-')}-{timestamp}.pdf"
        
        pdf_path = PDFGenerator.generate_pdf(substituted, filename, self.documents_dir)
        
        # Return document info
        download_url = f"/api/documents/download/{doc_id}"
        
        return doc_id, filename, download_url
    
    def get_document_path(self, document_id: str) -> Path:
        """Get path to a generated document by ID."""
        # List documents and find by ID prefix
        for pdf_file in self.documents_dir.glob("*.pdf"):
            if document_id in pdf_file.stem:
                return pdf_file
        
        raise FileNotFoundError(f"Document not found: {document_id}")
