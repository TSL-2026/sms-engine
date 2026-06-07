import csv
import io
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime, timezone
from sms_engine.models import Hazard, RiskAssessment
from sms_engine.database import hazards as hazards_db, risk_assessments as risk_db
from sms_engine.risk_matrix import assess_risk
from sms_engine.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1")


@router.post("/operator/{tenant_id}/hazards")
def create_hazard(tenant_id: str, hazard: Hazard, user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    hazard.tenant_id = tenant_id
    hazard.created_by = user.user_id
    hazard.status = "open"
    count = len(hazards_db.list({"tenant_id": tenant_id}))
    year = datetime.now(timezone.utc).strftime("%Y")
    hazard.hazard_id = f"HR-{year}-{count + 1:04d}"
    doc_id = hazards_db.add(hazard.model_dump())
    return {"id": doc_id, "hazard_id": hazard.hazard_id, "status": "open"}


@router.get("/operator/{tenant_id}/hazards")
def list_hazards(tenant_id: str, status: str = "", user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    filters = {"tenant_id": tenant_id}
    if status:
        filters["status"] = status
    return hazards_db.list(filters)


@router.get("/operator/{tenant_id}/hazards/{hazard_id}")
def get_hazard(tenant_id: str, hazard_id: str, user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    hazard = hazards_db.get(hazard_id)
    if not hazard or hazard.get("tenant_id") != tenant_id:
        raise HTTPException(404, "Hazard not found")
    assessments = risk_db.list({"hazard_id": hazard_id})
    return {"hazard": hazard, "risk_assessments": assessments}


@router.post("/operator/{tenant_id}/hazards/{hazard_id}/risk")
def assess_hazard_risk(tenant_id: str, hazard_id: str, assessment: RiskAssessment,
                       user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    hazard = hazards_db.get(hazard_id)
    if not hazard or hazard.get("tenant_id") != tenant_id:
        raise HTTPException(404, "Hazard not found")
    result = assess_risk(assessment.severity, assessment.likelihood)
    assessment.hazard_id = hazard_id
    assessment.assessed_by = user.user_id
    assessment.risk_index = result["risk_index"]
    assessment.risk_zone = result["risk_zone"]
    doc_id = risk_db.add(assessment.model_dump())
    return {"id": doc_id, **result}


@router.post("/operator/{tenant_id}/hazards/import")
async def import_hazards_csv(tenant_id: str, file: UploadFile = File(...),
                             user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files accepted")
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    errors = []
    existing = len(hazards_db.list({"tenant_id": tenant_id}))
    year = datetime.now(timezone.utc).strftime("%Y")
    for i, row in enumerate(reader, start=2):
        try:
            existing += 1
            hazard_id = f"HR-{year}-{existing:04d}"
            hazard = Hazard(
                tenant_id=tenant_id,
                hazard_id=hazard_id,
                title=row.get("title", "Imported hazard"),
                description=row.get("description", ""),
                category=row.get("category", ""),
                status=row.get("status", "open"),
                created_by=user.user_id,
            )
            hazards_db.add(hazard.model_dump())
            imported += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})
    return {"imported": imported, "errors": errors, "total_rows": imported + len(errors)}
