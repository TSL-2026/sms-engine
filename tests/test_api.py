import pytest
from fastapi.testclient import TestClient
from aviation.api.main import app

client = TestClient(app)


class TestAPI:
    def test_health(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["version"] == "2.1.0"

    def test_health_alias(self):
        for ep in ["/health", "/ping"]:
            r = client.get(ep)
            assert r.status_code == 200
            assert r.json()["status"] == "online"

    def test_status_page(self):
        r = client.get("/status/status.html")
        assert r.status_code == 200
        assert "SMS-Engine Status" in r.text

    def test_docs(self):
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200
        assert client.get("/openapi.json").status_code == 200

    def test_assess_flight_low_risk(self):
        response = client.post("/assess-flight", json={
            "scenario": "Pilot rested, VFR conditions, familiar airport"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["decision"]["state"] == "CLEARED"

    def test_assess_flight_high_risk(self):
        response = client.post("/assess-flight", json={
            "scenario": (
                "Pilot severely fatigued, strong crosswinds, "
                "mountainous terrain, hydraulic leak, management pressure"
            )
        })
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["decision"]["state"] in (
            "CONDITIONAL_OPERATION", "BLOCKED_BY_SAFETY_ENGINE"
        )

    def test_assess_flight_invalid_input(self):
        response = client.post("/assess-flight", json={"scenario": ""})
        assert response.status_code == 200
        assert response.json()["result"]["decision"]["state"] == "ERROR"

    def test_assess_flight_missing_field(self):
        response = client.post("/assess-flight", json={})
        assert response.status_code == 422

    def test_safety_report(self):
        response = client.get("/safety-report")
        assert response.status_code == 200
        assert "metrics" in response.json()

    def test_history(self):
        r = client.get("/history")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "assessments" in data

    def test_assessments_alias(self):
        r = client.get("/assessments?limit=10")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 0

    def test_simulate(self):
        response = client.post("/simulate", json={
            "scenarios": ["Severe turbulence", "Perfect VFR day"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_requested"] == 2
        assert len(data["results"]) == 2
