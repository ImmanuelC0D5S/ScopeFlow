"""Retrieve node - RAG from pgvector."""
from typing import Optional
from backend.db.vector import similarity_search


def retrieve_context(
    project_id: str,
    query: str,
    query_vector: Optional[list[float]] = None,
    limit: int = 5
) -> list[str]:
    """
    Retrieve relevant context from vector database.
    
    Args:
        project_id: UUID of the project
        query: Query text (used if query_vector not provided)
        query_vector: Pre-computed embedding vector
        limit: Maximum number of results
        
    Returns:
        List of relevant text chunks
    """
    if not query_vector:
        # If no vector provided, return empty list
        # In production, you would generate embeddings here
        return []
    
    try:
        results = similarity_search(
            query_vector=query_vector,
            project_id=project_id,
            limit=limit,
            threshold=0.7
        )
        
        # Extract just the text from results
        context_chunks = [result["text"] for result in results]
        
        return context_chunks
        
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return []


def retrieve_baseline_context(project_id: str) -> dict:
    """
    Retrieve the active baseline for a project.
    
    Args:
        project_id: UUID of the project
        
    Returns:
        Dictionary with baseline data
    """
    from backend.db.baseline_repository import BaselineRepository
    
    repository = BaselineRepository()
    baseline = repository.get_active_baseline(project_id)
    
    return baseline or {}

# Made with Bob
