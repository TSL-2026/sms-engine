import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
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


class FlightScenario(BaseModel):
    scenario: str


class BatchScenario(BaseModel):
    scenarios: list[str]


@app.get("/")
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
