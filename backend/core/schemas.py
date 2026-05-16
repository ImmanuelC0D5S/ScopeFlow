from enum import Enum
from typing import Optional, Annotated

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    scope_change = "scope_change"
    clarification = "clarification"
    admin = "admin"
    ambiguous = "ambiguous"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RecommendedAction(str, Enum):
    auto_approve = "auto_approve"
    flag_for_pm = "flag_for_pm"
    ignore = "ignore"


class ScopeChangeExtraction(BaseModel):
    type: ChangeType
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    affects_deliverable: Optional[str] = None
    detail: str = Field(min_length=1, max_length=500)
    explicitly_excluded: bool
    new_deliverable: bool
    effort_delta_hours: Optional[Annotated[float, Field(ge=0.0)]] = None
    dollar_impact: Optional[Annotated[float, Field(ge=0.0)]] = None
    risk_level: RiskLevel
    recommended_action: RecommendedAction
    reasoning: str = Field(min_length=1, max_length=500)


class IngestMessageRequest(BaseModel):
    channel: str = Field(min_length=1, max_length=20)
    sender: str = Field(min_length=1, max_length=255)
    message_body: str = Field(min_length=1)
    thread_id: Optional[str] = Field(default=None, max_length=255)
    workspace_id: Optional[str] = Field(default=None, max_length=255)


class IngestMessageResponse(BaseModel):
    routing_status: str
    project_id: Optional[str] = None


# Baseline schemas
class Deliverable(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=500)
    estimated_hours: Optional[float] = None
    due_date: Optional[str] = None
    status: str = Field(default="active")


class Milestone(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    date: Optional[str] = None
    deliverables: list[str] = Field(default_factory=list)


class ScopeBaseline(BaseModel):
    deliverables: list[Deliverable] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    total_contract_value: float = 0.0
    currency: str = Field(default="USD", max_length=3)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class BaselineResponse(BaseModel):
    project_id: str
    version: int
    baseline: ScopeBaseline
    is_active: bool
    created_at: str
    candidate_project_ids: list[str] = Field(default_factory=list)
