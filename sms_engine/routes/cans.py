from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from pydantic import BaseModel
from sms_engine.models import CAN, CAP, VALID_CAN_TRANSITIONS, VALID_CAP_TRANSITIONS, VALID_HAZARD_TRANSITIONS
from sms_engine.database import cans as cans_db, caps as caps_db, hazards as hazards_db
from sms_engine.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1")


def _validate_transition(current: str, new: str, transitions: dict) -> None:
    allowed = transitions.get(current, [])
    if new not in allowed:
        raise HTTPException(
            400,
            f"Invalid status transition: '{current}' -> '{new}'. Allowed: {allowed or 'none (terminal state)'}",
        )


@router.post("/operator/{tenant_id}/hazards/{hazard_id}/can")
def issue_can(tenant_id: str, hazard_id: str, can: CAN,
              user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    hazard = hazards_db.get(hazard_id)
    if not hazard or hazard.get("tenant_id") != tenant_id:
        raise HTTPException(404, "Hazard not found")
    can.tenant_id = tenant_id
    can.hazard_id = hazard_id
    can.issued_by = user.user_id
    can.status = "Issued"
    can.updated_at = datetime.now(timezone.utc).isoformat()
    count = len(cans_db.list({"tenant_id": tenant_id}))
    year = datetime.now(timezone.utc).strftime("%Y")
    can.can_id = f"CAN-{year}-{count + 1:04d}"
    doc_id = cans_db.add(can.model_dump())
    hazards_db.update(hazard_id, {"status": "processing"})
    return {"id": doc_id, "can_id": can.can_id, "status": "Issued"}


@router.get("/operator/{tenant_id}/cans")
def list_cans(tenant_id: str, status: str = "", user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    filters = {"tenant_id": tenant_id}
    if status:
        filters["status"] = status
    return cans_db.list(filters)


@router.post("/operator/{tenant_id}/cans/{can_id}/cap")
def submit_cap(tenant_id: str, can_id: str, cap: CAP,
               user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    can = cans_db.get(can_id)
    if not can or can.get("tenant_id") != tenant_id:
        raise HTTPException(404, "CAN not found")
    now = datetime.now(timezone.utc).isoformat()
    cap.can_id = can_id
    cap.tenant_id = tenant_id
    cap.submitted_by = user.user_id
    cap.status = "Submitted"
    cap.updated_at = now
    count = len(caps_db.list({"tenant_id": tenant_id}))
    year = datetime.now(timezone.utc).strftime("%Y")
    cap.cap_id = f"CAP-{year}-{count + 1:04d}"
    doc_id = caps_db.add(cap.model_dump())
    cans_db.update(can_id, {"status": "Accepted", "updated_at": now})
    return {"id": doc_id, "cap_id": cap.cap_id, "status": "Submitted", "message": "CAP submitted for review"}


@router.get("/operator/{tenant_id}/cans/{can_id}/cap")
def get_cap(tenant_id: str, can_id: str, user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    results = caps_db.list({"can_id": can_id})
    if not results:
        raise HTTPException(404, "CAP not found")
    return results[0]


class VerifyRequest(BaseModel):
    verdict: str  # accepted | ineffective | returned
    notes: str = ""


@router.post("/operator/{tenant_id}/caps/{cap_id}/verify")
def verify_cap(tenant_id: str, cap_id: str, body: VerifyRequest,
               user: CurrentUser = Depends(get_current_user)):
    verdict = body.verdict
    notes = body.notes
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    results = caps_db.list({"can_id": cap_id})
    if not results:
        raise HTTPException(404, "CAP not found")
    cap = results[0]
    can_record = cans_db.get(cap.get("can_id", ""))
    if not can_record or can_record.get("tenant_id") != tenant_id:
        raise HTTPException(404, "CAN not found")
    hazard_id = can_record.get("hazard_id", "")
    now = datetime.now(timezone.utc).isoformat()

    if verdict == "accepted":
        caps_db.update(cap["id"], {"status": "Completed", "completed_date": now,
                                    "review_notes": notes, "reviewed_by": user.user_id, "updated_at": now})
        cans_db.update(cap["can_id"], {"status": "Accepted", "updated_at": now})
        hazards_db.update(hazard_id, {"status": "closed", "closed_at": now, "closed_by": user.user_id})
        return {"verdict": "accepted", "hazard_status": "closed", "message": "CAP verified effective, hazard closed"}
    elif verdict == "ineffective":
        caps_db.update(cap["id"], {"status": "Rejected", "rejection_reason": notes,
                                    "reviewed_by": user.user_id, "updated_at": now})
        cans_db.update(cap["can_id"], {"status": "Rejected", "updated_at": now})
        hazards_db.update(hazard_id, {"status": "reopened"})
        return {"verdict": "ineffective", "hazard_status": "reopened",
                "message": "CAP ineffective, hazard reopened for corrective action"}
    elif verdict == "returned":
        caps_db.update(cap["id"], {"status": "Draft", "rejection_reason": notes,
                                    "reviewed_by": user.user_id, "updated_at": now})
        cans_db.update(cap["can_id"], {"status": "Issued", "updated_at": now})
        hazards_db.update(hazard_id, {"status": "open"})
        return {"verdict": "returned", "hazard_status": "open",
                "message": "CAP returned for revision, hazard set back to open"}
    else:
        raise HTTPException(400, "verdict must be: accepted, ineffective, or returned")


@router.patch("/operator/{tenant_id}/cans/{can_id}/status")
def update_can_status(tenant_id: str, can_id: str, status: str,
                      user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    can = cans_db.get(can_id)
    if not can or can.get("tenant_id") != tenant_id:
        raise HTTPException(404, "CAN not found")
    _validate_transition(can.get("status", "Draft"), status, VALID_CAN_TRANSITIONS)
    now = datetime.now(timezone.utc).isoformat()
    cans_db.update(can_id, {"status": status, "updated_at": now})
    return {"can_id": can_id, "status": status, "updated_at": now}


@router.patch("/operator/{tenant_id}/cans/{can_id}/cap/review")
def review_cap(tenant_id: str, can_id: str, status: str, notes: str = "",
               user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    results = caps_db.list({"can_id": can_id})
    if not results:
        raise HTTPException(404, "CAP not found")
    cap = results[0]
    _validate_transition(cap.get("status", "Draft"), status, VALID_CAP_TRANSITIONS)
    now = datetime.now(timezone.utc).isoformat()
    update_data = {"status": status, "updated_at": now, "reviewed_by": user.user_id, "review_notes": notes}
    if status == "Approved":
        update_data["approved_by"] = user.user_id
        update_data["approved_date"] = now
        cans_db.update(can_id, {"status": "Accepted", "updated_at": now})
    elif status == "Rejected":
        update_data["rejection_reason"] = notes
        cans_db.update(can_id, {"status": "Rejected", "updated_at": now})
    elif status == "Completed":
        update_data["completed_date"] = now
        cans_db.update(can_id, {"status": "Accepted", "updated_at": now})
        from sms_engine.database import hazards as hdb
        can_record = cans_db.get(can_id)
        if can_record:
            hazard_id = can_record.get("hazard_id", "")
            if hazard_id:
                hdb.update(hazard_id, {"status": "closed", "closed_at": now, "closed_by": user.user_id})
    caps_db.update(cap["id"], update_data)
    return {"status": status, "message": f"CAP {status}"}
