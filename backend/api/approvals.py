"""Approval endpoints for PM review."""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel
from backend.core.audit import log_approval_decision

router = APIRouter(prefix="/approvals", tags=["approvals"])


# In-memory storage for demo (in production, use database)
pending_approvals = {}
approval_history = []


class ApprovalRequest(BaseModel):
    """Request body for approval actions."""
    notes: Optional[str] = None


class ScopeChangeApproval(BaseModel):
    """Scope change approval data."""
    id: str
    project_id: str
    message_id: str
    sender: str
    message_body: str
    extracted_data: dict
    routing_decision: dict
    status: str  # "pending", "approved", "rejected"
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    notes: Optional[str] = None


@router.get("/pending")
async def get_pending_approvals(
    project_id: Optional[str] = None
) -> list[ScopeChangeApproval]:
    """
    Get all pending approvals, optionally filtered by project.
    
    Args:
        project_id: Optional project UUID to filter by
        
    Returns:
        List of pending approvals
    """
    approvals = [
        approval for approval in pending_approvals.values()
        if approval["status"] == "pending"
    ]
    
    if project_id:
        approvals = [
            approval for approval in approvals
            if approval["project_id"] == project_id
        ]
    
    return approvals


@router.get("/{approval_id}")
async def get_approval(approval_id: str) -> ScopeChangeApproval:
    """
    Get a specific approval by ID.
    
    Args:
        approval_id: UUID of the approval
        
    Returns:
        Approval data
    """
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    return pending_approvals[approval_id]


@router.post("/{approval_id}/approve")
async def approve_change(
    approval_id: str,
    request: ApprovalRequest,
    x_pm_user: str = Header(..., alias="X-PM-User")
) -> dict:
    """
    Approve a scope change.
    
    Args:
        approval_id: UUID of the approval
        request: Approval request with optional notes
        x_pm_user: PM user ID from header
        
    Returns:
        Success message
    """
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = pending_approvals[approval_id]
    
    if approval["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Approval already {approval['status']}"
        )
    
    # Update approval status
    from datetime import datetime
    approval["status"] = "approved"
    approval["reviewed_at"] = datetime.utcnow().isoformat()
    approval["reviewed_by"] = x_pm_user
    approval["notes"] = request.notes
    
    # Log to audit
    log_approval_decision(
        approval_id=approval_id,
        decision="approved",
        actor=x_pm_user,
        project_id=approval["project_id"],
        notes=request.notes
    )
    
    # Add to history
    approval_history.append(approval.copy())
    
    # TODO: Trigger executors here
    # from backend.executors import run_executors
    # run_executors(approval)
    
    return {
        "status": "approved",
        "approval_id": approval_id,
        "reviewed_by": x_pm_user
    }


@router.post("/{approval_id}/reject")
async def reject_change(
    approval_id: str,
    request: ApprovalRequest,
    x_pm_user: str = Header(..., alias="X-PM-User")
) -> dict:
    """
    Reject a scope change.
    
    Args:
        approval_id: UUID of the approval
        request: Rejection request with optional notes
        x_pm_user: PM user ID from header
        
    Returns:
        Success message
    """
    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = pending_approvals[approval_id]
    
    if approval["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Approval already {approval['status']}"
        )
    
    # Update approval status
    from datetime import datetime
    approval["status"] = "rejected"
    approval["reviewed_at"] = datetime.utcnow().isoformat()
    approval["reviewed_by"] = x_pm_user
    approval["notes"] = request.notes
    
    # Log to audit
    log_approval_decision(
        approval_id=approval_id,
        decision="rejected",
        actor=x_pm_user,
        project_id=approval["project_id"],
        notes=request.notes
    )
    
    # Add to history
    approval_history.append(approval.copy())
    
    return {
        "status": "rejected",
        "approval_id": approval_id,
        "reviewed_by": x_pm_user
    }


@router.get("/history")
async def get_approval_history(
    project_id: Optional[str] = None,
    limit: int = 50
) -> list[ScopeChangeApproval]:
    """
    Get approval history, optionally filtered by project.
    
    Args:
        project_id: Optional project UUID to filter by
        limit: Maximum number of results
        
    Returns:
        List of historical approvals
    """
    history = approval_history.copy()
    
    if project_id:
        history = [
            approval for approval in history
            if approval["project_id"] == project_id
        ]
    
    # Sort by reviewed_at descending
    history.sort(key=lambda x: x.get("reviewed_at", ""), reverse=True)
    
    return history[:limit]


def create_approval(
    project_id: str,
    message_id: str,
    sender: str,
    message_body: str,
    extracted_data: dict,
    routing_decision: dict
) -> str:
    """
    Create a new approval request.
    
    Args:
        project_id: UUID of the project
        message_id: ID of the message
        sender: Message sender
        message_body: Message text
        extracted_data: Extracted scope change data
        routing_decision: Routing decision from agent
        
    Returns:
        UUID of the created approval
    """
    from uuid import uuid4
    from datetime import datetime
    
    approval_id = str(uuid4())
    
    approval = {
        "id": approval_id,
        "project_id": project_id,
        "message_id": message_id,
        "sender": sender,
        "message_body": message_body,
        "extracted_data": extracted_data,
        "routing_decision": routing_decision,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "reviewed_at": None,
        "reviewed_by": None,
        "notes": None
    }
    
    pending_approvals[approval_id] = approval
    
    return approval_id

# Made with Bob
