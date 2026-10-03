import re
from pathlib import Path
from typing import Dict, List, Tuple


class FieldType:
    TEXT = "text"
    DATE = "date"
    TEXTAREA = "textarea"
    SELECT = "select"
    EMAIL = "email"


class TemplateParser:
    """Parse templates and extract field definitions."""
    
    FIELD_PATTERN = r'<span class="coverpage_link">([^<]+)</span>'
    
    PREDEFINED_FIELDS = {
        "Purpose": {
            "type": FieldType.TEXTAREA,
            "label": "Purpose of Disclosure",
            "required": True,
            "description": "The purpose for which Confidential Information will be disclosed",
        },
        "Effective Date": {
            "type": FieldType.DATE,
            "label": "Effective Date",
            "required": True,
            "description": "Date when the NDA becomes effective",
        },
        "MNDA Term": {
            "type": FieldType.TEXT,
            "label": "MNDA Term",
            "required": True,
            "description": "Duration of the agreement (e.g., '1 year', '2 years')",
            "placeholder": "1 year",
        },
        "Term of Confidentiality": {
            "type": FieldType.TEXT,
            "label": "Term of Confidentiality",
            "required": True,
            "description": "How long confidentiality obligations survive",
            "placeholder": "3 years after termination",
        },
        "Governing Law": {
            "type": FieldType.SELECT,
            "label": "Governing Law",
            "required": True,
            "description": "State or jurisdiction whose laws govern the agreement",
            "options": ["California", "New York", "Delaware", "Texas", "Other"],
        },
        "Jurisdiction": {
            "type": FieldType.TEXT,
            "label": "Jurisdiction",
            "required": True,
            "description": "Courts with exclusive jurisdiction",
            "placeholder": "California",
        },
    }
    
    @staticmethod
    def load_template(template_path: Path) -> str:
        """Load a template file."""
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text(encoding='utf-8')
    
    @staticmethod
    def extract_fields(template_content: str) -> List[str]:
        """Extract field names from template."""
        matches = re.findall(TemplateParser.FIELD_PATTERN, template_content)
        return matches
    
    @staticmethod
    def get_field_schema(field_name: str) -> Dict:
        """Get field schema for a field name."""
        if field_name in TemplateParser.PREDEFINED_FIELDS:
            return TemplateParser.PREDEFINED_FIELDS[field_name]
        
        return {
            "type": FieldType.TEXT,
            "label": field_name,
            "required": True,
            "description": f"Enter {field_name.lower()}",
        }
    
    @staticmethod
    def extract_schema(template_content: str) -> Dict[str, Dict]:
        """Extract complete schema for a template."""
        fields = TemplateParser.extract_fields(template_content)
        schema = {}
        for field in fields:
            schema[field] = TemplateParser.get_field_schema(field)
        return schema
    
    @staticmethod
    def substitute_fields(template_content: str, field_values: Dict[str, str]) -> str:
        """Substitute field values in template."""
        result = template_content
        extracted_fields = TemplateParser.extract_fields(template_content)
        
        for field in extracted_fields:
            if field in field_values:
                value = field_values[field]
                pattern = f'<span class="coverpage_link">{re.escape(field)}</span>'
                result = re.sub(pattern, value, result)
        
        return result
    
    @staticmethod
    def validate_fields(template_content: str, field_values: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate that all required fields are provided."""
        extracted_fields = TemplateParser.extract_fields(template_content)
        missing_fields = []
        
        for field in extracted_fields:
            if field not in field_values or not str(field_values[field]).strip():
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
