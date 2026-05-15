# ============================================================
# File: aviation/risk/risk_matrix.py
# Version: v1.0.0
# ICAO Doc 9859 aligned Risk Matrix Engine
# ============================================================

class RiskMatrixEngine:
    """
    Implements ICAO-style risk assessment:

    Risk = Likelihood × Severity

    Range:
    - Likelihood: 1 (Rare) → 5 (Frequent)
    - Severity: 1 (Negligible) → 5 (Catastrophic)
    """

    # -----------------------------
    # PUBLIC API
    # -----------------------------
    def evaluate(self, likelihood: int, severity: int):
        score = likelihood * severity
        level, decision = self._classify(score)

        return {
            "likelihood": likelihood,
            "severity": severity,
            "score": score,
            "risk_level": level,
            "decision": decision
        }

    # -----------------------------
    # CLASSIFICATION LOGIC
    # -----------------------------
    def _classify(self, score: int):
        if score <= 4:
            return "LOW", "ACCEPT"
        elif score <= 9:
            return "MEDIUM", "REVIEW"
        elif score <= 16:
            return "HIGH", "MITIGATION REQUIRED"
        else:
            return "EXTREME", "NO-GO"