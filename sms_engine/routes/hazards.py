import csv
import io
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime, timezone
from sms_engine.models import Hazard, RiskAssessment, VALID_HAZARD_TRANSITIONS
from sms_engine.database import hazards as hazards_db, risk_assessments as risk_db
from sms_engine.risk_matrix import assess_risk
from sms_engine.hazard_import import extract_hazards_from_excel, get_risk_distribution
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


@router.post("/operator/{tenant_id}/hazards/import-excel")
async def import_hazards_excel(tenant_id: str, file: UploadFile = File(...),
                               user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(400, "Only Excel files (.xlsx/.xls) accepted")

    import pandas as pd

    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = {"title": "title", "description": "description", "category": "category",
               "severity": "severity", "likelihood": "likelihood", "source_report_id": "source_report_ids"}

    imported = 0
    errors = []
    existing = len(hazards_db.list({"tenant_id": tenant_id}))
    year = datetime.now(timezone.utc).strftime("%Y")

    for i, (_, row) in enumerate(df.iterrows(), start=2):
        try:
            existing += 1
            title = str(row.get("title", row.get("hazard", "Imported hazard"))).strip()
            if not title or title == "nan":
                title = "Imported hazard"

            description = str(row.get("description", row.get("desc", ""))).strip()
            if description == "nan":
                description = ""
            category = str(row.get("category", row.get("cat", ""))).strip()
            if category == "nan":
                category = ""
            source = str(row.get("source_report_id", row.get("source_report", ""))).strip()
            source_ids = [source] if source and source != "nan" else []

            hazard_id = f"HR-{year}-{existing:04d}"
            hazard = Hazard(
                tenant_id=tenant_id,
                hazard_id=hazard_id,
                title=title,
                description=description,
                category=category,
                source_report_ids=source_ids,
                status="open",
                created_by=user.user_id,
            )
            doc_id = hazards_db.add(hazard.model_dump())

            raw_severity = row.get("severity", row.get("sev", ""))
            raw_likelihood = row.get("likelihood", row.get("like", ""))

            risk_result = None
            if pd.notna(raw_severity) and pd.notna(raw_likelihood):
                severity_val = str(raw_severity).strip().upper()
                try:
                    likelihood_val = int(float(str(raw_likelihood).strip()))
                except (ValueError, TypeError):
                    likelihood_val = 0
                if severity_val in {"A", "B", "C", "D", "E"} and likelihood_val in {1, 2, 3, 4, 5}:
                    risk_result = assess_risk(severity_val, likelihood_val)
                    assessment = RiskAssessment(
                        hazard_id=doc_id,
                        assessed_by=user.user_id,
                        severity=severity_val,
                        likelihood=likelihood_val,
                        risk_index=risk_result["risk_index"],
                        risk_zone=risk_result["risk_zone"],
                        rationale=f"Auto-calculated from Excel import (severity={severity_val}, likelihood={likelihood_val})",
                    )
                    risk_db.add(assessment.model_dump())

            imported += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    return {
        "imported": imported,
        "errors": errors,
        "total_rows": imported + len(errors),
        "note": "Hazards with severity and likelihood columns received auto risk calculation per ICAO Doc 9859",
    }


@router.post("/operator/{tenant_id}/hazards/import-from-excel")
async def import_hazards_from_excel(
    tenant_id: str,
    file: UploadFile = File(...),
    dry_run: bool = False,
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(400, "Only Excel files (.xlsx/.xls) accepted")

    content = await file.read()
    hazards = extract_hazards_from_excel(content)

    if not hazards:
        return {
            "imported": 0,
            "errors": [],
            "total_rows": 0,
            "note": "No hazard rows found in the sheet. Ensure the hazard identification column has checkmarks (✔, TRUE, Yes, 1).",
        }

    if dry_run:
        dist = get_risk_distribution(hazards)
        return {
            "dry_run": True,
            "total_found": len(hazards),
            "hazards": hazards,
            "risk_distribution": dist,
        }

    imported = 0
    errors = []
    existing = len(hazards_db.list({"tenant_id": tenant_id}))
    year = datetime.now(timezone.utc).strftime("%Y")

    for h in hazards:
        try:
            existing += 1
            hazard_id = f"HR-{year}-{existing:04d}"
            hazard_doc = {
                "tenant_id": tenant_id,
                "hazard_id": hazard_id,
                "title": h["description"][:80] or "Imported hazard",
                "description": h["description"],
                "category": h["source_type"],
                "source_type": h["source_type"],
                "reported_date": h["reported_date"],
                "department": h["department"],
                "remarks": h["remarks"],
                "status": "open",
                "created_by": user.user_id,
            }
            doc_id = hazards_db.add(hazard_doc)

            risk = h["risk_assessment"]
            assessment = {
                "hazard_id": doc_id,
                "assessed_by": user.user_id,
                "severity": risk["severity"],
                "likelihood": risk["likelihood"],
                "risk_index": risk["risk_index"],
                "risk_zone": risk["risk_zone"],
                "rationale": f"Auto-calculated from description keyword analysis (severity={risk['severity_label']}, likelihood={risk['likelihood_label']})",
            }
            risk_db.add(assessment)
            imported += 1
        except Exception as e:
            errors.append({"description_preview": h["description"][:50], "error": str(e)})

    dist = get_risk_distribution(hazards)
    return {
        "imported": imported,
        "errors": errors,
        "total_found": len(hazards),
        "risk_distribution": dist,
        "note": "Risk calculated via ICAO keyword analysis on description text",
    }


def _validate_transition(current: str, new: str, transitions: dict) -> None:
    allowed = transitions.get(current, [])
    if new not in allowed:
        from fastapi import HTTPException
        raise HTTPException(
            400,
            f"Invalid hazard status transition: '{current}' -> '{new}'. Allowed: {allowed or 'none (terminal state)'}",
        )


@router.post("/operator/{tenant_id}/hazards/{hazard_id}/close")
def close_hazard(tenant_id: str, hazard_id: str, lessons_learned: str = "",
                 user: CurrentUser = Depends(get_current_user)):
    if not user.can_access_tenant(tenant_id):
        raise HTTPException(403, "Access denied")
    hazard = hazards_db.get(hazard_id)
    if not hazard or hazard.get("tenant_id") != tenant_id:
        raise HTTPException(404, "Hazard not found")
    _validate_transition(hazard.get("status", "open"), "closed", VALID_HAZARD_TRANSITIONS)
    now = datetime.now(timezone.utc).isoformat()
    hazards_db.update(hazard_id, {
        "status": "closed",
        "closed_at": now,
        "closed_by": user.user_id,
        "lessons_learned": lessons_learned,
    })
    return {
        "hazard_id": hazard.get("hazard_id", hazard_id),
        "status": "closed",
        "closed_at": now,
        "lessons_learned": lessons_learned,
        "message": "Hazard closed and archived",
    }
