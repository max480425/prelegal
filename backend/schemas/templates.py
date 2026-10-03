from pydantic import BaseModel
from typing import Dict, List, Any, Optional


class FieldMetadata(BaseModel):
    """Metadata about a template field."""
    type: str
    label: str
    required: bool
    description: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None


class TemplateMetadata(BaseModel):
    """Metadata about a template."""
    name: str
    description: str
    fields: Dict[str, FieldMetadata]


class TemplateListItem(BaseModel):
    """Item in template list."""
    name: str
    description: str
