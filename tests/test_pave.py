import pytest
from aviation.risk.pave import evaluate_pave


class TestPAVE:
    def test_no_flags(self):
        result = evaluate_pave("Perfect conditions, familiar airport")
        assert result["environment"] == []
        assert result["aircraft"] == []
        assert result["pilot"] == []
        assert result["external"] == []

    def test_adverse_weather(self):
        result = evaluate_pave("Heavy thunderstorms and severe icing conditions")
        assert any("weather" in str(f).lower() or "icing" in str(f).lower()
                   for f in result["environment"])

    def test_aircraft_issues(self):
        result = evaluate_pave("Aircraft has engine problems and hydraulic failure")
        assert len(result["aircraft"]) > 0

    def test_external_pressure(self):
        result = evaluate_pave("Management pressuring pilot to complete delivery on time")
        assert len(result["external"]) > 0

    def test_mountainous_terrain(self):
        result = evaluate_pave("Approach into mountainous terrain airport")
        assert any("terrain" in str(f).lower() for f in result["environment"])
