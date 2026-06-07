import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aviation.core.system import AviationSafetySystem
from aviation.storage.firestore_client import FirestoreStorage
from aviation.api.docs import configure_docs


system = AviationSafetySystem()
storage = FirestoreStorage()

app = FastAPI(
    title="Aviation Safety Intelligence API",
    version="2.1.0"
)
configure_docs(app)

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(frontend_dir), html=True), name="dashboard")

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/status", StaticFiles(directory=str(static_dir), html=True), name="status")


rate_limit_store: dict[str, list[datetime]] = defaultdict(list)


class FlightScenario(BaseModel):
    scenario: str


class BatchScenario(BaseModel):
    scenarios: list[str]


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing_page():
    landing_path = frontend_dir / "landing.html"
    if landing_path.exists():
        html = landing_path.read_text()
        public_url = os.getenv("PUBLIC_API_URL", "https://sms-engine-660696925387.us-central1.run.app")
        html = html.replace("PUBLIC_API_URL_PLACEHOLDER", public_url)
        return HTMLResponse(content=html)
    return {
        "status": "online",
        "system": "Aviation Safety Intelligence System",
        "version": "2.1.0",
        "docs": "/docs",
        "dashboard": "/dashboard/"
    }


@app.get("/health")
@app.get("/healthz")
@app.get("/ping")
async def health():
    return {
        "status": "online",
        "system": "Aviation Safety Intelligence System",
        "version": "2.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/assess-flight")
def assess_flight(request: FlightScenario):
    result = system.assess_flight(request.scenario)

    storage.save_assessment({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenario": request.scenario,
        "risk_score": result.get("decision", {}).get("risk_score"),
        "risk_level": result.get("decision", {}).get("risk_level"),
        "decision": result.get("decision", {}).get("state")
    })

    return {
        "input": request.scenario,
        "result": result
    }


@app.get("/safety-report", tags=["analytics"])
def safety_report():
    stats = system.generate_safety_report()
    if stats.get("total_assessments") is None:
        stats["total_assessments"] = 0
    return stats


@app.get("/history")
@app.get("/assessments")
def list_assessments(limit: int = 50):
    assessments = storage.get_recent(limit=min(limit, 200))
    return {
        "total": len(assessments),
        "assessments": assessments
    }


@app.post("/simulate", tags=["assessment"])
def simulate(request: BatchScenario):
    unique = list(set(s.strip() for s in request.scenarios if s.strip()))
    requested = len(request.scenarios)
    total_unique = len(unique)

    results = []
    cache_hits = 0
    for s in unique:
        cached = system.cache.get(s)
        if cached:
            results.append(cached)
            cache_hits += 1
        else:
            result = system.assess_flight(s)
            results.append(result)

    return {
        "total_requested": requested,
        "unique_processed": total_unique,
        "duplicates_removed": requested - total_unique,
        "cache_hit_rate": round(cache_hits / total_unique, 2) if total_unique else 0,
        "results": results
    }


@app.post("/public/assess-flight", tags=["public"])
async def public_assess_flight(request: Request):
    """
    Public demo endpoint with rate limiting.
    10 requests/minute per IP for landing page demos.
    """
    body = await request.json()
    scenario = body.get("scenario", "").strip()
    if not scenario:
        raise HTTPException(status_code=422, detail="scenario is required")

    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)

    if ip in rate_limit_store:
        rate_limit_store[ip] = [ts for ts in rate_limit_store[ip] if now - ts < timedelta(minutes=1)]

    if ip in rate_limit_store and len(rate_limit_store[ip]) >= 10:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

    if ip not in rate_limit_store:
        rate_limit_store[ip] = []
    rate_limit_store[ip].append(now)

    result = system.assess_flight(scenario)

    return {
        "input": scenario,
        "decision": result.get("decision", {}),
        "ai_explanation": result.get("ai_explanation", ""),
        "risk_level": result.get("decision", {}).get("risk_level", "UNKNOWN"),
        "risk_score": result.get("decision", {}).get("risk_score", 0),
    }
