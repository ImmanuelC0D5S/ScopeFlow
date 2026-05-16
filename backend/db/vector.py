"""Vector database operations using pgvector."""
from uuid import UUID, uuid4
from typing import Optional
import psycopg
from backend.core.config import settings


def _to_driver_dsn(database_url: str) -> str:
    """Convert SQLAlchemy-style DSN to psycopg DSN."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url


def init_pgvector() -> None:
    """
    Initialize pgvector extension and create embeddings table.
    Run this once during setup.
    """
    dsn = _to_driver_dsn(settings.database_url)
    
    with psycopg.connect(dsn, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create embeddings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contract_embeddings (
                    id UUID PRIMARY KEY,
                    project_id UUID NOT NULL REFERENCES projects(id),
                    chunk_text TEXT NOT NULL,
                    chunk_index INT NOT NULL,
                    embedding vector(1536),
                    metadata JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            
            # Create index for similarity search
            cur.execute("""
                CREATE INDEX IF NOT EXISTS contract_embeddings_vector_idx 
                ON contract_embeddings 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            
            # Create index for project lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS contract_embeddings_project_idx 
                ON contract_embeddings (project_id)
            """)
            
            conn.commit()


def upsert_embedding(
    project_id: str,
    text: str,
    vector: list[float],
    chunk_index: int = 0,
    metadata: Optional[dict] = None
) -> None:
    """
    Insert or update an embedding in the vector database.
    
    Args:
        project_id: UUID of the project
        text: The text chunk
        vector: Embedding vector (1536 dimensions for OpenAI)
        chunk_index: Index of this chunk in the document
        metadata: Optional metadata dict
    """
    dsn = _to_driver_dsn(settings.database_url)
    
    # Validate vector dimensions
    if len(vector) != 1536:
        raise ValueError(f"Expected 1536-dimensional vector, got {len(vector)}")
    
    with psycopg.connect(dsn, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO contract_embeddings 
                (id, project_id, chunk_text, chunk_index, embedding, metadata)
                VALUES (%s, %s::uuid, %s, %s, %s::vector, %s::jsonb)
                """,
                (
                    uuid4(),
                    project_id,
                    text,
                    chunk_index,
                    vector,
                    metadata or {}
                )
            )
            conn.commit()


def batch_upsert_embeddings(
    project_id: str,
    chunks: list[str],
    vectors: list[list[float]],
    metadata: Optional[dict] = None
) -> int:
    """
    Batch insert embeddings for multiple chunks.
    
    Args:
        project_id: UUID of the project
        chunks: List of text chunks
        vectors: List of embedding vectors
        metadata: Optional metadata dict applied to all chunks
        
    Returns:
        Number of embeddings inserted
    """
    if len(chunks) != len(vectors):
        raise ValueError("Number of chunks must match number of vectors")
    
    dsn = _to_driver_dsn(settings.database_url)
    
    with psycopg.connect(dsn, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                if len(vector) != 1536:
                    raise ValueError(f"Expected 1536-dimensional vector at index {i}, got {len(vector)}")
                
                cur.execute(
                    """
                    INSERT INTO contract_embeddings 
                    (id, project_id, chunk_text, chunk_index, embedding, metadata)
                    VALUES (%s, %s::uuid, %s, %s, %s::vector, %s::jsonb)
                    """,
                    (
                        uuid4(),
                        project_id,
                        chunk,
                        i,
                        vector,
                        metadata or {}
                    )
                )
            
            conn.commit()
    
    return len(chunks)


def similarity_search(
    query_vector: list[float],
    project_id: Optional[str] = None,
    limit: int = 5,
    threshold: float = 0.7
) -> list[dict]:
    """
    Search for similar text chunks using cosine similarity.
    
    Args:
        query_vector: Query embedding vector
        project_id: Optional project UUID to filter results
        limit: Maximum number of results
        threshold: Minimum similarity threshold (0-1)
        
    Returns:
        List of dicts with 'text', 'similarity', 'metadata'
    """
    if len(query_vector) != 1536:
        raise ValueError(f"Expected 1536-dimensional vector, got {len(query_vector)}")
    
    dsn = _to_driver_dsn(settings.database_url)
    
    with psycopg.connect(dsn, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            if project_id:
                query = """
                    SELECT 
                        chunk_text,
                        1 - (embedding <=> %s::vector) as similarity,
                        metadata
                    FROM contract_embeddings
                    WHERE project_id = %s::uuid
                        AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                cur.execute(query, (query_vector, project_id, query_vector, threshold, query_vector, limit))
            else:
                query = """
                    SELECT 
                        chunk_text,
                        1 - (embedding <=> %s::vector) as similarity,
                        metadata
                    FROM contract_embeddings
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                cur.execute(query, (query_vector, query_vector, threshold, query_vector, limit))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "text": row[0],
                    "similarity": float(row[1]),
                    "metadata": row[2] or {}
                })
            
            return results


def delete_project_embeddings(project_id: str) -> int:
    """
    Delete all embeddings for a project.
    
    Args:
        project_id: UUID of the project
        
    Returns:
        Number of embeddings deleted
    """
    dsn = _to_driver_dsn(settings.database_url)
    
    with psycopg.connect(dsn, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM contract_embeddings WHERE project_id = %s::uuid",
                (project_id,)
            )
            deleted_count = cur.rowcount
            conn.commit()
            
            return deleted_count

# Made with Bob
