import pytest
from aviation.risk.risk_matrix import RiskMatrixEngine


class TestRiskMatrix:
    def setup_method(self):
        self.engine = RiskMatrixEngine()

    def test_low_risk(self):
        result = self.engine.evaluate(1, 1)
        assert result["score"] == 1
        assert result["risk_level"] == "LOW"
        assert result["decision"] == "ACCEPT"

    def test_medium_risk(self):
        result = self.engine.evaluate(2, 3)
        assert result["score"] == 6
        assert result["risk_level"] == "MEDIUM"
        assert result["decision"] == "REVIEW"

    def test_high_risk(self):
        result = self.engine.evaluate(4, 3)
        assert result["score"] == 12
        assert result["risk_level"] == "HIGH"
        assert result["decision"] == "MITIGATION REQUIRED"

    def test_extreme_risk(self):
        result = self.engine.evaluate(5, 5)
        assert result["score"] == 25
        assert result["risk_level"] == "EXTREME"
        assert result["decision"] == "NO-GO"

    def test_score_bounds(self):
        result = self.engine.evaluate(5, 5)
        assert result["likelihood"] == 5
        assert result["severity"] == 5
        assert result["score"] == 25
