from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.db.baseline_repository import BaselineRepository
from backend.core.schemas import ScopeBaseline, BaselineResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_id}/baseline")
async def get_project_baseline(project_id: str) -> dict:
    """
    Get the active baseline for a project.
    
    Args:
        project_id: UUID of the project
        
    Returns:
        Baseline data with deliverables and exclusions
    """
    repository = BaselineRepository()
    
    try:
        baseline = repository.get_active_baseline(project_id)
        
        if not baseline:
            raise HTTPException(
                status_code=404,
                detail=f"No active baseline found for project {project_id}"
            )
        
        return baseline
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database error: {str(exc)}"
        ) from exc


@router.put("/{project_id}/baseline/{baseline_id}")
async def update_project_baseline(
    project_id: str,
    baseline_id: str,
    baseline: ScopeBaseline
) -> dict:
    """
    Update an existing baseline (PM confirms/edits).
    
    Args:
        project_id: UUID of the project
        baseline_id: UUID of the baseline
        baseline: Updated baseline data
        
    Returns:
        Success message
    """
    repository = BaselineRepository()
    
    try:
        success = repository.update_baseline(baseline_id, baseline)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Baseline {baseline_id} not found"
            )
        
        return {
            "status": "updated",
            "project_id": project_id,
            "baseline_id": baseline_id
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database error: {str(exc)}"
        ) from exc


@router.post("/{project_id}/baseline")
async def create_project_baseline(
    project_id: str,
    baseline: ScopeBaseline,
    source_doc_id: Optional[str] = None
) -> dict:
    """
    Create a new baseline for a project.
    
    Args:
        project_id: UUID of the project
        baseline: Baseline data with deliverables and exclusions
        source_doc_id: Optional ID of the source document
        
    Returns:
        Created baseline ID
    """
    repository = BaselineRepository()
    
    try:
        baseline_id = repository.create_baseline(
            project_id=project_id,
            baseline=baseline,
            source_doc_id=source_doc_id
        )
        
        return {
            "status": "created",
            "project_id": project_id,
            "baseline_id": baseline_id
        }
        
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database error: {str(exc)}"
        ) from exc

# Made with Bob
