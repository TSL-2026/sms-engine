from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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


LANDING = Path(__file__).resolve().parent.parent / "frontend_sms" / "landing.html"


@app.get("/", response_class=HTMLResponse)
def root():
    if LANDING.exists():
        return HTMLResponse(content=LANDING.read_text())
    return {"system": "AviaSafe SMS", "version": "3.0.0"}


mount_frontend(app)
