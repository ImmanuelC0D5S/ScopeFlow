from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Form
from typing import Optional

from backend.core.schemas import IngestMessageRequest, IngestMessageResponse
from backend.db.routing_repository import PostgresRoutingRepository
from backend.ingestion.routing import resolve_project_for_message
from backend.ingestion.parser import parse_document
from backend.ingestion.clause_segmenter import split_clauses
from backend.ingestion.ner import extract_entities
from backend.ingestion.chunker import chunk_by_clauses
from backend.db.vector import batch_upsert_embeddings

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/message", response_model=IngestMessageResponse)
async def ingest_message(payload: IngestMessageRequest) -> IngestMessageResponse:
    repository = PostgresRoutingRepository()
    try:
        decision = resolve_project_for_message(
            repository=repository,
            channel=payload.channel,
            sender=payload.sender,
            thread_id=payload.thread_id,
            workspace_id=payload.workspace_id,
            raw_message=payload.message_body,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    return IngestMessageResponse(
        routing_status=decision.status,
        project_id=decision.project_id,
        candidate_project_ids=decision.candidate_project_ids,
    )


@router.post("/unrouted/{unrouted_id}/assign")
async def assign_unrouted_message(
    unrouted_id: str,
    project_id: str,
    x_pm_user: str | None = Header(default=None, alias="X-PM-User"),
) -> dict[str, str]:
    if not x_pm_user:
        raise HTTPException(status_code=400, detail="X-PM-User header is required")

    repository = PostgresRoutingRepository()
    try:
        repository.assign_unrouted_message(
            unrouted_id=unrouted_id,
            project_id=project_id,
            pm_user_id=x_pm_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc

    return {"status": "routed"}


@router.post("/contract")
async def ingest_contract(
    file: UploadFile = File(...),
    project_id: str = Form(...),
) -> dict:
    """
    Upload and process a contract document (PDF or DOCX).
    
    Steps:
    1. Parse document to extract text
    2. Segment into clauses
    3. Extract named entities
    4. Chunk text for embeddings
    5. Store chunks in vector database (placeholder - needs OpenAI API)
    
    Args:
        file: Contract file (PDF or DOCX)
        project_id: UUID of the project
        
    Returns:
        Status dict with processing results
    """
    try:
        # Read file content
        content = await file.read()
        filename = file.filename or ""
        
        # Step 1: Parse document
        text = parse_document(content, filename)
        
        if not text or len(text) < 100:
            raise HTTPException(status_code=400, detail="Document appears to be empty or too short")
        
        # Step 2: Segment into clauses
        clauses = split_clauses(text)
        
        # Step 3: Extract named entities
        entities = extract_entities(text)
        
        # Step 4: Chunk text for embeddings
        chunks = chunk_by_clauses(clauses, size=1000, overlap=200)
        
        # Step 5: Store in vector database (placeholder)
        # Note: This requires OpenAI API key to generate embeddings
        # For now, we'll just return the processing results
        
        return {
            "status": "processed",
            "project_id": project_id,
            "filename": filename,
            "text_length": len(text),
            "clauses_count": len(clauses),
            "chunks_count": len(chunks),
            "entities": {
                "parties": len(entities.get("parties", [])),
                "dates": len(entities.get("dates", [])),
                "amounts": len(entities.get("amounts", [])),
                "scope_terms": len(entities.get("scope_terms", [])),
            }
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error processing contract: {str(exc)}") from exc

# Made with Bob
