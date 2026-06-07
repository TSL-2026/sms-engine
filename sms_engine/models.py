from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Tenant(BaseModel):
    id: str = ""
    name: str
    code: str  # ICAO 3-letter code
    fleet: str = ""
    base: str = ""
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
    status: str = "open"  # open | processing | closed | reopened
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: str = ""
    created_by: str = ""
    closed_by: str = ""
    lessons_learned: str = ""


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


class CAN(BaseModel):
    id: str = ""
    can_id: str = ""  # CAN-YYYY-NNNN
    tenant_id: str = ""
    hazard_id: str = ""  # Reference to originating hazard
    issued_by: str = ""  # Safety Manager name
    issued_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    due_date: str = ""
    priority: str = "Medium"  # High / Medium / Low
    description: str = ""
    department_assigned: str = ""
    status: str = "Draft"  # Draft | Issued | Accepted | Rejected | Expired
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ActionItem(BaseModel):
    id: str = ""
    action: str
    owner: str
    target_date: str = ""
    status: str = "pending"  # pending | in_progress | completed
    completed_date: str = ""
    notes: str = ""


class CAP(BaseModel):
    id: str = ""
    cap_id: str = ""  # CAP-YYYY-NNNN
    tenant_id: str = ""
    can_id: str = ""  # Reference to parent CAN
    submitted_by: str = ""  # Responsible Manager name
    submitted_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action_items: list[dict] = []
    resource_requirements: str = ""
    proposed_timeline: str = ""  # e.g. "30 days"
    status: str = "Draft"  # Draft | Submitted | Approved | InProgress | Completed | Rejected
    rejection_reason: str = ""
    approved_by: str = ""
    approved_date: str = ""
    completed_date: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


VALID_HAZARD_TRANSITIONS = {
    "open": ["processing"],
    "processing": ["closed", "reopened", "open"],
    "closed": [],
    "reopened": ["processing", "closed"],
}

VALID_CAN_TRANSITIONS = {
    "Draft": ["Issued"],
    "Issued": ["Accepted", "Rejected", "Expired"],
    "Accepted": ["Expired"],
    "Rejected": ["Draft", "Expired"],
    "Expired": [],
}

VALID_CAP_TRANSITIONS = {
    "Draft": ["Submitted"],
    "Submitted": ["Approved", "Rejected"],
    "Approved": ["InProgress", "Completed", "Rejected"],
    "InProgress": ["Completed", "Rejected"],
    "Completed": [],
    "Rejected": ["Draft", "Submitted"],
}
