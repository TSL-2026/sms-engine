from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Tenant(BaseModel):
    id: str = ""
    name: str
    code: str  # ICAO 3-letter code
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class User(BaseModel):
    id: str = ""
    tenant_id: str = ""
    email: str
    name: str
    role: str = "reporter"  # regulator | safety_manager | dept_head | reporter | safety_officer
    department: str = ""
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Report(BaseModel):
    id: str = ""
    tenant_id: str = ""
    report_type: str  # VSR or MOR
    status: str = "submitted"  # submitted | under_review | triaged | escalated_to_hazard | closed
    submitted_by: str = ""
    occurrence_date: str = ""
    location: str = ""
    description: str
    initial_severity: str = ""
    confidentiality: bool = True  # VSR is confidential by default
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_by: str = ""
    review_notes: str = ""
    hazard_id: str = ""  # link to Hazard if escalated


class Hazard(BaseModel):
    id: str = ""
    tenant_id: str = ""
    hazard_id: str = ""  # HR-YYYY-NNNN
    title: str
    description: str
    category: str = ""  # operational | technical | organizational | human_factors | environmental
    source_report_ids: list[str] = []
    status: str = "open"  # open | under_mitigation | closed | accepted
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: str = ""
    created_by: str = ""


class RiskAssessment(BaseModel):
    id: str = ""
    hazard_id: str = ""
    assessed_by: str = ""
    severity: str = ""  # A | B | C | D | E
    likelihood: int = 0  # 1 | 2 | 3 | 4 | 5
    risk_index: str = ""  # e.g. "3B"
    risk_zone: str = ""  # intolerable | tolerable | acceptable
    rationale: str = ""
    assessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CorrectiveActionNotice(BaseModel):
    id: str = ""
    tenant_id: str = ""
    hazard_id: str = ""
    can_id: str = ""  # CAN-YYYY-NNNN
    issued_by: str = ""
    department: str = ""
    due_date: str = ""
    priority: str = "routine"  # immediate | urgent | routine | observation
    description: str
    status: str = "open"  # open | awaiting_cap | cap_received | closed
    issued_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: str = ""


class ActionItem(BaseModel):
    action: str
    owner: str
    target_date: str = ""
    status: str = "pending"  # pending | in_progress | completed


class CorrectiveActionPlan(BaseModel):
    id: str = ""
    can_id: str = ""
    submitted_by: str = ""
    status: str = "submitted"  # draft | submitted | under_review | approved | rejected | implemented
    description: str = ""
    action_items: list[ActionItem] = []
    resource_requirements: str = ""
    submitted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_by: str = ""
    review_notes: str = ""
    approved_at: str = ""
