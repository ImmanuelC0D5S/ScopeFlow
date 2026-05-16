"""Audit logging for ScopeFlow."""
import json
from datetime import datetime
from typing import Any, Optional
import psycopg
from backend.core.config import settings


def _to_driver_dsn(database_url: str) -> str:
    """Convert SQLAlchemy-style DSN to psycopg DSN."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url


def write_audit_log(
    event_type: str,
    actor: str,
    payload: dict[str, Any],
    project_id: Optional[str] = None
) -> None:
    """
    Write an audit log entry to the database.
    
    Args:
        event_type: Type of event (e.g., "approval_approved", "approval_rejected")
        actor: User ID or system identifier
        payload: Event data as dictionary
        project_id: Optional project UUID
    """
    # For now, just print to console
    # In production, this would write to a database table
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "actor": actor,
        "project_id": project_id,
        "payload": payload
    }
    
    print(f"[AUDIT] {json.dumps(log_entry)}")
    
    # TODO: Write to audit_logs table in database
    # CREATE TABLE audit_logs (
    #     id UUID PRIMARY KEY,
    #     timestamp TIMESTAMPTZ NOT NULL,
    #     event_type TEXT NOT NULL,
    #     actor TEXT NOT NULL,
    #     project_id UUID,
    #     payload JSONB NOT NULL
    # );


def log_approval_decision(
    approval_id: str,
    decision: str,
    actor: str,
    project_id: Optional[str] = None,
    notes: Optional[str] = None
) -> None:
    """
    Log an approval decision (approved/rejected).
    
    Args:
        approval_id: UUID of the approval
        decision: "approved" or "rejected"
        actor: User ID making the decision
        project_id: Optional project UUID
        notes: Optional notes from PM
    """
    event_type = f"approval_{decision}"
    payload = {
        "approval_id": approval_id,
        "decision": decision,
        "notes": notes
    }
    
    write_audit_log(event_type, actor, payload, project_id)


def log_scope_change_detected(
    project_id: str,
    message_id: str,
    extracted_data: dict,
    routing_decision: dict
) -> None:
    """
    Log when a scope change is detected.
    
    Args:
        project_id: UUID of the project
        message_id: ID of the message
        extracted_data: Extracted scope change data
        routing_decision: Routing decision from agent
    """
    payload = {
        "message_id": message_id,
        "change_type": extracted_data.get("type"),
        "confidence": extracted_data.get("confidence"),
        "final_action": routing_decision.get("final_action"),
        "reason_codes": routing_decision.get("reason_codes", [])
    }
    
    write_audit_log("scope_change_detected", "system", payload, project_id)


def log_executor_run(
    executor_type: str,
    project_id: str,
    approval_id: str,
    success: bool,
    details: Optional[dict] = None
) -> None:
    """
    Log when an executor runs.
    
    Args:
        executor_type: Type of executor (jira, slack, notion, billing)
        project_id: UUID of the project
        approval_id: UUID of the approval
        success: Whether execution was successful
        details: Optional execution details
    """
    payload = {
        "executor_type": executor_type,
        "approval_id": approval_id,
        "success": success,
        "details": details or {}
    }
    
    write_audit_log(f"executor_{executor_type}", "system", payload, project_id)

# Made with Bob
