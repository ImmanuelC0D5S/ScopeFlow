"""Repository for baseline operations."""
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime
import psycopg
from backend.core.config import settings
from backend.core.schemas import ScopeBaseline, Deliverable, Milestone


def _to_driver_dsn(database_url: str) -> str:
    """Convert SQLAlchemy-style DSN to psycopg DSN."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url


class BaselineRepository:
    """Repository for managing project baselines."""
    
    def __init__(self, dsn: Optional[str] = None):
        self._dsn = _to_driver_dsn(dsn or settings.database_url)
        self._connect_timeout = 3
    
    def create_baseline(
        self,
        project_id: str,
        baseline: ScopeBaseline,
        source_doc_id: Optional[str] = None
    ) -> str:
        """
        Create a new baseline for a project.
        
        Args:
            project_id: UUID of the project
            baseline: ScopeBaseline object with deliverables, milestones, exclusions
            source_doc_id: Optional ID of the source document
            
        Returns:
            UUID of the created baseline
        """
        baseline_id = uuid4()
        
        with psycopg.connect(self._dsn, connect_timeout=self._connect_timeout) as conn:
            with conn.cursor() as cur:
                # Get next version number
                cur.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM project_baselines WHERE project_id = %s::uuid",
                    (project_id,)
                )
                version = cur.fetchone()[0]
                
                # Deactivate previous baselines
                cur.execute(
                    "UPDATE project_baselines SET is_active = FALSE WHERE project_id = %s::uuid",
                    (project_id,)
                )
                
                # Insert new baseline
                cur.execute(
                    """
                    INSERT INTO project_baselines 
                    (id, project_id, version, source_doc_id, is_active)
                    VALUES (%s, %s::uuid, %s, %s, TRUE)
                    """,
                    (baseline_id, project_id, version, source_doc_id)
                )
                
                # Insert deliverables
                for deliverable in baseline.deliverables:
                    cur.execute(
                        """
                        INSERT INTO baseline_deliverables
                        (id, baseline_id, deliverable_code, description, estimated_hours, due_date, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            uuid4(),
                            baseline_id,
                            deliverable.code,
                            deliverable.description,
                            deliverable.estimated_hours,
                            deliverable.due_date,
                            deliverable.status
                        )
                    )
                
                # Insert exclusions
                for exclusion in baseline.exclusions:
                    cur.execute(
                        """
                        INSERT INTO baseline_exclusions
                        (id, baseline_id, description)
                        VALUES (%s, %s, %s)
                        """,
                        (uuid4(), baseline_id, exclusion)
                    )
                
                conn.commit()
        
        return str(baseline_id)
    
    def get_active_baseline(self, project_id: str) -> Optional[dict]:
        """
        Get the active baseline for a project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Dictionary with baseline data or None if not found
        """
        with psycopg.connect(self._dsn, connect_timeout=self._connect_timeout) as conn:
            with conn.cursor() as cur:
                # Get baseline
                cur.execute(
                    """
                    SELECT id, version, created_at
                    FROM project_baselines
                    WHERE project_id = %s::uuid AND is_active = TRUE
                    LIMIT 1
                    """,
                    (project_id,)
                )
                baseline_row = cur.fetchone()
                
                if not baseline_row:
                    return None
                
                baseline_id, version, created_at = baseline_row
                
                # Get deliverables
                cur.execute(
                    """
                    SELECT deliverable_code, description, estimated_hours, due_date, status
                    FROM baseline_deliverables
                    WHERE baseline_id = %s
                    ORDER BY deliverable_code
                    """,
                    (baseline_id,)
                )
                deliverables = [
                    {
                        "code": row[0],
                        "description": row[1],
                        "estimated_hours": row[2],
                        "due_date": row[3],
                        "status": row[4]
                    }
                    for row in cur.fetchall()
                ]
                
                # Get exclusions
                cur.execute(
                    """
                    SELECT description
                    FROM baseline_exclusions
                    WHERE baseline_id = %s
                    """,
                    (baseline_id,)
                )
                exclusions = [row[0] for row in cur.fetchall()]
                
                return {
                    "project_id": project_id,
                    "baseline_id": str(baseline_id),
                    "version": version,
                    "deliverables": deliverables,
                    "exclusions": exclusions,
                    "created_at": created_at.isoformat(),
                    "is_active": True
                }
    
    def update_baseline(
        self,
        baseline_id: str,
        baseline: ScopeBaseline
    ) -> bool:
        """
        Update an existing baseline (deliverables and exclusions).
        
        Args:
            baseline_id: UUID of the baseline
            baseline: Updated ScopeBaseline object
            
        Returns:
            True if successful, False otherwise
        """
        with psycopg.connect(self._dsn, connect_timeout=self._connect_timeout) as conn:
            with conn.cursor() as cur:
                # Delete existing deliverables and exclusions
                cur.execute(
                    "DELETE FROM baseline_deliverables WHERE baseline_id = %s",
                    (UUID(baseline_id),)
                )
                cur.execute(
                    "DELETE FROM baseline_exclusions WHERE baseline_id = %s",
                    (UUID(baseline_id),)
                )
                
                # Insert updated deliverables
                for deliverable in baseline.deliverables:
                    cur.execute(
                        """
                        INSERT INTO baseline_deliverables
                        (id, baseline_id, deliverable_code, description, estimated_hours, due_date, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            uuid4(),
                            UUID(baseline_id),
                            deliverable.code,
                            deliverable.description,
                            deliverable.estimated_hours,
                            deliverable.due_date,
                            deliverable.status
                        )
                    )
                
                # Insert updated exclusions
                for exclusion in baseline.exclusions:
                    cur.execute(
                        """
                        INSERT INTO baseline_exclusions
                        (id, baseline_id, description)
                        VALUES (%s, %s, %s)
                        """,
                        (uuid4(), UUID(baseline_id), exclusion)
                    )
                
                conn.commit()
        
        return True

# Made with Bob
