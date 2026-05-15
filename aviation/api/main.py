# ============================================================
# File: aviation/api/main.py
# Version: v2.1.0
#
# Module: Aviation Safety API Layer
#
# Purpose:
#   Exposes Aviation Safety System via REST API
# ============================================================

from fastapi import FastAPI
from pydantic import BaseModel

from aviation.core.system import AviationSafetySystem


# Initialize system
system = AviationSafetySystem()

app = FastAPI(
    title="Aviation Safety Intelligence API",
    version="2.1.0"
)


# ============================================================
# Request Models
# ============================================================

class FlightScenario(BaseModel):
    scenario: str


class BatchScenario(BaseModel):
    scenarios: list[str]


# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/")
def health():
    return {
        "status": "online",
        "system": "Aviation Safety Intelligence System",
        "version": "2.1.0"
    }


# ============================================================
# REAL-TIME RISK ASSESSMENT
# ============================================================
@app.post("/assess-flight")
def assess_flight(request: FlightScenario):

    result = system.assess_flight(request.scenario)

    return {
        "input": request.scenario,
        "result": result
    }


# ============================================================
# SAFETY INTELLIGENCE REPORT
# ============================================================
@app.get("/safety-report")
def safety_report():

    return system.generate_safety_report()


# ============================================================
# BATCH SIMULATION ENGINE
# ============================================================
@app.post("/simulate")
def simulate(request: BatchScenario):

    results = system.simulate_scenarios(request.scenarios)

    return {
        "total_scenarios": len(request.scenarios),
        "results": results
    }