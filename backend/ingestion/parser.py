"""Document parser for PDF and DOCX files."""
import io
from typing import BinaryIO


def parse_document(raw: bytes, filename: str = "") -> str:
    """
    Parse PDF or DOCX document and extract text.
    
    Args:
        raw: Raw bytes of the document
        filename: Optional filename to determine document type
        
    Returns:
        Extracted text content
    """
    # Determine file type from filename or content
    if filename.lower().endswith('.pdf') or raw.startswith(b'%PDF'):
        return _parse_pdf(raw)
    elif filename.lower().endswith('.docx') or raw.startswith(b'PK'):
        return _parse_docx(raw)
    else:
        # Fallback to plain text
        return raw.decode(errors="ignore")


def _parse_pdf(raw: bytes) -> str:
    """Extract text from PDF using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        
        pdf_file = io.BytesIO(raw)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    except ImportError:
        # Fallback if PyPDF2 not installed
        return raw.decode(errors="ignore")
    except Exception as e:
        # Log error and return empty string
        print(f"Error parsing PDF: {e}")
        return ""


def _parse_docx(raw: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        
        docx_file = io.BytesIO(raw)
        doc = Document(docx_file)
        
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return "\n\n".join(text_parts)
    except ImportError:
        # Fallback if python-docx not installed
        return raw.decode(errors="ignore")
    except Exception as e:
        # Log error and return empty string
        print(f"Error parsing DOCX: {e}")
        return ""

# Made with Bob
