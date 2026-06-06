import pytest
from unittest.mock import patch


class TestDispatcher:
    def test_low_risk_cleared(self, dispatcher, sample_low_risk_scenario):
        result = dispatcher.run(sample_low_risk_scenario)
        assert result["decision"]["state"] == "CLEARED"
        assert result["decision"]["risk_level"] == "LOW"
        assert result["decision"]["risk_score"] == 1

    def test_high_risk_conditional(self, dispatcher, sample_high_risk_scenario):
        result = dispatcher.run(sample_high_risk_scenario)
        assert result["decision"]["state"] == "CONDITIONAL_OPERATION"
        assert result["decision"]["risk_level"] == "HIGH"

    def test_invalid_input(self, dispatcher):
        result = dispatcher.run("")
        assert result["decision"]["state"] == "ERROR"

    def test_structured_output_schema(self, dispatcher, sample_low_risk_scenario):
        result = dispatcher.run(sample_low_risk_scenario)
        assert "timestamp" in result
        assert "decision" in result
        assert "risk_factors" in result
        assert "mitigations" in result
        assert "imsafe_flags" in result["risk_factors"]
        assert "pave_flags" in result["risk_factors"]

    def test_mitigations_present(self, dispatcher, sample_high_risk_scenario):
        result = dispatcher.run(sample_high_risk_scenario)
        assert len(result["mitigations"]) > 0

    def test_ai_explanation_fallback(self, dispatcher, sample_low_risk_scenario):
        """AI call fails gracefully when API key is invalid"""
        result = dispatcher.run(sample_low_risk_scenario)
        assert "ai_explanation" in result
