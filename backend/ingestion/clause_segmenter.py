"""Clause segmentation for contract documents."""
import re


def split_clauses(text: str) -> list[str]:
    """
    Split contract text into logical clauses using regex and heuristics.
    
    Identifies clauses based on:
    - Numbered sections (1., 1.1, etc.)
    - Lettered sections (a), (b), etc.
    - Headers in ALL CAPS
    - Double line breaks
    
    Args:
        text: Full contract text
        
    Returns:
        List of clause strings
    """
    if not text or not text.strip():
        return []
    
    clauses = []
    
    # Split by numbered sections (e.g., "1.", "1.1", "2.3.4")
    # Pattern matches: "1. ", "1.1 ", "2.3.4 " at start of line
    numbered_pattern = r'\n(\d+(?:\.\d+)*\.?\s+[A-Z])'
    parts = re.split(numbered_pattern, text)
    
    # Reconstruct clauses from split parts
    current_clause = parts[0].strip() if parts else ""
    
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            # Save previous clause if it has content
            if current_clause:
                clauses.append(current_clause)
            # Start new clause with the number/letter and content
            current_clause = parts[i] + parts[i + 1]
    
    # Add the last clause
    if current_clause:
        clauses.append(current_clause.strip())
    
    # If no numbered sections found, fall back to paragraph splitting
    if len(clauses) <= 1:
        clauses = _split_by_paragraphs(text)
    
    # Clean up clauses
    cleaned_clauses = []
    for clause in clauses:
        clause = clause.strip()
        # Skip very short clauses (likely headers or noise)
        if len(clause) > 20:
            cleaned_clauses.append(clause)
    
    return cleaned_clauses


def _split_by_paragraphs(text: str) -> list[str]:
    """Fallback: split by double line breaks."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    # Further split very long paragraphs
    result = []
    for para in paragraphs:
        if len(para) > 2000:
            # Split long paragraphs by single line breaks
            sub_parts = [s.strip() for s in para.split("\n") if s.strip()]
            result.extend(sub_parts)
        else:
            result.append(para)
    
    return result


def extract_section_headers(text: str) -> list[tuple[str, int]]:
    """
    Extract section headers and their positions in the text.
    
    Returns:
        List of (header_text, position) tuples
    """
    headers = []
    
    # Pattern for ALL CAPS headers (at least 3 words, all caps)
    caps_pattern = r'\n([A-Z][A-Z\s]{10,})\n'
    
    for match in re.finditer(caps_pattern, text):
        header = match.group(1).strip()
        position = match.start()
        headers.append((header, position))
    
    return headers

# Made with Bob
