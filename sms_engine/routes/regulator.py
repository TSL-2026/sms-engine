from fastapi import APIRouter, HTTPException, Depends
from sms_engine.database import tenants, reports, hazards, cans
from sms_engine.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1/regulator")


@router.get("/dashboard")
def regulator_dashboard(user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    all_tenants = tenants.list()
    dashboard = []
    for t in all_tenants:
        tid = t["id"]
        dashboard.append({
            "tenant": t,
            "report_count": len(reports.list({"tenant_id": tid})),
            "open_hazard_count": len([
                h for h in _all_hazards()
                if h.get("tenant_id") == tid and h.get("status") == "open"
            ]),
            "open_can_count": len([
                c for c in _all_cans()
                if c.get("tenant_id") == tid and c.get("status") != "closed"
            ]),
        })
    return {"tenants": dashboard}


@router.get("/operators")
def list_operators(user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    return tenants.list()


def _all_hazards():
    from sms_engine.database import hazards as hdb
    return hdb.list()


def _all_cans():
    from sms_engine.database import cans as cdb
    return cdb.list()
