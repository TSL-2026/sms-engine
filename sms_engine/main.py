from fastapi import FastAPI
from sms_engine.frontend import mount_frontend
from sms_engine.routes import reports, hazards, cans, regulator, tenants

app = FastAPI(
    title="AviaSafe — Safety Management System",
    description="Multi-tenant SMS aligned with ICAO Annex 19 / Doc 9859",
    version="3.0.0",
)

app.include_router(reports.router)
app.include_router(hazards.router)
app.include_router(cans.router)
app.include_router(regulator.router)
app.include_router(tenants.router)


@app.get("/health")
def health():
    return {"status": "ok", "system": "AviaSafe SMS", "version": "3.0.0"}


@app.get("/")
def root():
    return {
        "system": "AviaSafe SMS",
        "version": "3.0.0",
        "docs": "/docs",
        "endpoints": {
            "reports": "POST/GET /api/v1/operator/{tenant_id}/reports",
            "hazards": "POST/GET /api/v1/operator/{tenant_id}/hazards",
            "risk_assessment": "POST /api/v1/operator/{tenant_id}/hazards/{id}/risk",
            "cans": "POST/GET /api/v1/operator/{tenant_id}/cans",
            "cap": "POST /api/v1/operator/{tenant_id}/cans/{id}/cap",
            "regulator_dashboard": "GET /api/v1/regulator/dashboard",
        },
    }


mount_frontend(app)
