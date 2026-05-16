"""Clause-aware text chunking for embeddings."""
from typing import List


def chunk_text(text: str, size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Chunk text into overlapping segments, respecting clause boundaries.
    
    Args:
        text: Text to chunk
        size: Target chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    # If text is smaller than chunk size, return as single chunk
    if len(text) <= size:
        return [text.strip()]
    
    chunks = []
    
    # Split into sentences first (respects natural boundaries)
    sentences = _split_into_sentences(text)
    
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # If adding this sentence exceeds size, save current chunk
        if current_length + sentence_length > size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            # Keep last few sentences for context
            overlap_sentences = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_length += len(s)
                else:
                    break
            
            current_chunk = overlap_sentences
            current_length = overlap_length
        
        # Add sentence to current chunk
        current_chunk.append(sentence)
        current_length += sentence_length
    
    # Add final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(chunk_text)
    
    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences, handling common abbreviations.
    """
    import re
    
    # Replace common abbreviations to avoid false splits
    text = text.replace("Mr.", "Mr<dot>")
    text = text.replace("Mrs.", "Mrs<dot>")
    text = text.replace("Dr.", "Dr<dot>")
    text = text.replace("Inc.", "Inc<dot>")
    text = text.replace("Ltd.", "Ltd<dot>")
    text = text.replace("Co.", "Co<dot>")
    text = text.replace("Corp.", "Corp<dot>")
    text = text.replace("etc.", "etc<dot>")
    text = text.replace("e.g.", "e<dot>g<dot>")
    text = text.replace("i.e.", "i<dot>e<dot>")
    
    # Split on sentence boundaries (. ! ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Restore abbreviations
    sentences = [s.replace("<dot>", ".") for s in sentences]
    
    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def chunk_by_clauses(clauses: list[str], size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Chunk a list of clauses into larger segments.
    
    Useful when you already have clauses from clause_segmenter.
    
    Args:
        clauses: List of clause strings
        size: Target chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    if not clauses:
        return []
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for clause in clauses:
        clause_length = len(clause)
        
        # If single clause exceeds size, chunk it separately
        if clause_length > size:
            # Save current chunk first
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # Chunk the large clause
            sub_chunks = chunk_text(clause, size, overlap)
            chunks.extend(sub_chunks)
            continue
        
        # If adding this clause exceeds size, save current chunk
        if current_length + clause_length > size and current_chunk:
            chunks.append(" ".join(current_chunk))
            
            # Start new chunk with overlap (last clause)
            if overlap > 0 and current_chunk:
                current_chunk = [current_chunk[-1]]
                current_length = len(current_chunk[0])
            else:
                current_chunk = []
                current_length = 0
        
        # Add clause to current chunk
        current_chunk.append(clause)
        current_length += clause_length
    
    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Made with Bob
