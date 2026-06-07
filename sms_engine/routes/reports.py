from fastapi import APIRouter, HTTPException, Depends
from sms_engine.models import Report
from sms_engine.database import reports as reports_db
from sms_engine.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1")


@router.post("/operator/{tenant_id}/reports")
def submit_report(tenant_id: str, report: Report, user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    report.tenant_id = tenant_id
    report.submitted_by = user.user_id
    report.status = "submitted"
    doc_id = reports_db.add(report.model_dump())
    return {"id": doc_id, "status": "submitted", "message": "Report submitted successfully"}


@router.get("/operator/{tenant_id}/reports")
def list_reports(tenant_id: str, status: str = "", user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    filters = {"tenant_id": tenant_id}
    if status:
        filters["status"] = status
    return reports_db.list(filters)


@router.get("/operator/{tenant_id}/reports/{report_id}")
def get_report(tenant_id: str, report_id: str, user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    report = reports_db.get(report_id)
    if not report or report.get("tenant_id") != tenant_id:
        raise HTTPException(404, "Report not found")
    return report


@router.patch("/operator/{tenant_id}/reports/{report_id}/review")
def review_report(tenant_id: str, report_id: str, status: str, notes: str = "",
                  hazard_id: str = "", user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    report = reports_db.get(report_id)
    if not report or report.get("tenant_id") != tenant_id:
        raise HTTPException(404, "Report not found")
    update = {
        "status": status,
        "reviewed_by": user.user_id,
        "review_notes": notes,
    }
    if hazard_id:
        update["hazard_id"] = hazard_id
        update["status"] = "escalated_to_hazard"
    reports_db.update(report_id, update)
    return {"id": report_id, "status": update["status"], "message": "Report reviewed"}
