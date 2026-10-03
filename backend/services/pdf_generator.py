from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from io import BytesIO
from pathlib import Path


class PDFGenerator:
    """Generate PDFs from substituted templates."""
    
    @staticmethod
    def generate_pdf(content: str, filename: str, output_path: Path) -> Path:
        """Generate PDF from markdown content."""
        output_file = output_path / filename
        
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor='#000000',
            spaceAfter=12,
            spaceBefore=12,
            alignment=TA_LEFT,
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )
        
        # Parse content
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.1*inch))
            elif line.startswith('# '):
                title = line[2:].strip()
                story.append(Paragraph(title, title_style))
            elif line.startswith('## '):
                title = line[3:].strip()
                story.append(Paragraph(f'<b>{title}</b>', body_style))
            else:
                story.append(Paragraph(line, body_style))
        
        doc.build(story)
        return output_file
    
    @staticmethod
    def generate_pdf_bytes(content: str) -> bytes:
        """Generate PDF and return as bytes."""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*letter[0]/8.5,
            leftMargin=0.75*letter[0]/8.5,
            topMargin=0.75*letter[1]/11,
            bottomMargin=0.75*letter[1]/11,
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        )
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.05*inch))
            else:
                story.append(Paragraph(line, body_style))
        
        doc.build(story)
        return buffer.getvalue()
