import pytest
from aviation.human_factors.imsafe import evaluate_imsafe


class TestIMSAFE:
    def test_no_risk_flags(self):
        result = evaluate_imsafe("Pilot rested, well-fed, calm")
        assert result["risk_level"] == "LOW"
        assert result["risk_flags"] == []

    def test_fatigue_detected(self):
        result = evaluate_imsafe("Pilot is severely fatigued with only 2 hours of sleep")
        assert "Fatigue" in str(result["risk_flags"])

    def test_alcohol_detected(self):
        result = evaluate_imsafe("Pilot drank alcohol last night")
        assert "Alcohol" in str(result["risk_flags"])

    def test_multiple_flags(self):
        result = evaluate_imsafe(
            "Pilot is ill and stressed about family issues"
        )
        assert len(result["risk_flags"]) >= 2

    def test_empty_input(self):
        result = evaluate_imsafe("")
        assert result["risk_level"] == "LOW"
