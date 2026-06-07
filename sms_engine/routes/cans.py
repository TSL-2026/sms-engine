from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from sms_engine.models import CorrectiveActionNotice, CorrectiveActionPlan
from sms_engine.database import cans as cans_db, caps as caps_db, hazards as hazards_db
from sms_engine.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1")


@router.post("/operator/{tenant_id}/hazards/{hazard_id}/can")
def issue_can(tenant_id: str, hazard_id: str, can: CorrectiveActionNotice,
              user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    hazard = hazards_db.get(hazard_id)
    if not hazard or hazard.get("tenant_id") != tenant_id:
        raise HTTPException(404, "Hazard not found")
    can.tenant_id = tenant_id
    can.hazard_id = hazard_id
    can.issued_by = user.user_id
    can.status = "open"
    count = len(cans_db.list({"tenant_id": tenant_id}))
    year = datetime.now(timezone.utc).strftime("%Y")
    can.can_id = f"CAN-{year}-{count + 1:04d}"
    doc_id = cans_db.add(can.model_dump())
    hazards_db.update(hazard_id, {"status": "under_mitigation"})
    return {"id": doc_id, "can_id": can.can_id, "status": "open"}


@router.get("/operator/{tenant_id}/cans")
def list_cans(tenant_id: str, status: str = "", user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    filters = {"tenant_id": tenant_id}
    if status:
        filters["status"] = status
    return cans_db.list(filters)


@router.post("/operator/{tenant_id}/cans/{can_id}/cap")
def submit_cap(tenant_id: str, can_id: str, cap: CorrectiveActionPlan,
               user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    can = cans_db.get(can_id)
    if not can or can.get("tenant_id") != tenant_id:
        raise HTTPException(404, "CAN not found")
    cap.can_id = can_id
    cap.submitted_by = user.user_id
    cap.status = "submitted"
    doc_id = caps_db.add(cap.model_dump())
    cans_db.update(can_id, {"status": "awaiting_cap"})
    return {"id": doc_id, "status": "submitted", "message": "CAP submitted for review"}


@router.get("/operator/{tenant_id}/cans/{can_id}/cap")
def get_cap(tenant_id: str, can_id: str, user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    results = caps_db.list({"can_id": can_id})
    if not results:
        raise HTTPException(404, "CAP not found")
    return results[0]


@router.patch("/operator/{tenant_id}/cans/{can_id}/cap/review")
def review_cap(tenant_id: str, can_id: str, status: str, notes: str = "",
               user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    results = caps_db.list({"can_id": can_id})
    if not results:
        raise HTTPException(404, "CAP not found")
    cap = results[0]
    caps_db.update(cap["id"], {"status": status, "reviewed_by": user.user_id, "review_notes": notes})
    if status == "approved":
        caps_db.update(cap["id"], {"approved_at": datetime.now(timezone.utc).isoformat()})
        cans_db.update(can_id, {"status": "cap_received"})
    elif status == "implemented":
        cans_db.update(can_id, {"status": "closed", "closed_at": datetime.now(timezone.utc).isoformat()})
        from sms_engine.database import hazards as hdb
        can_record = cans_db.get(can_id)
        if can_record:
            hazard_id = can_record.get("hazard_id", "")
            if hazard_id:
                hdb.update(hazard_id, {"status": "closed", "closed_at": datetime.now(timezone.utc).isoformat()})
    return {"status": status, "message": f"CAP {status}"}
