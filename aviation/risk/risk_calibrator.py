# ============================================================
# File: aviation/risk/risk_calibrator.py
# Version: v1.0.0
# Risk Calibration Engine (Learning Layer)
# ============================================================

import os
import json
from collections import defaultdict


class RiskCalibrator:
    """
    Learns from historical audit logs to adjust risk sensitivity.

    This is NOT ML.
    This is rule adaptation based on observed patterns.
    """

    def __init__(self, log_dir="aviation_logs"):
        self.log_dir = log_dir

    # --------------------------------------------------------
    # Load all past decisions
    # --------------------------------------------------------
    def load_logs(self):
        logs = []

        if not os.path.exists(self.log_dir):
            return logs

        for file in os.listdir(self.log_dir):
            if file.endswith(".json"):
                path = os.path.join(self.log_dir, file)
                with open(path, "r") as f:
                    try:
                        logs.append(json.load(f))
                    except:
                        continue

        return logs

    # --------------------------------------------------------
    # Analyze risk patterns
    # --------------------------------------------------------
    def analyze_patterns(self):
        logs = self.load_logs()

        pattern_counts = defaultdict(int)
        high_risk_triggers = defaultdict(int)

        for log in logs:
            data = log.get("data", {})
            imsafe = data.get("imsafe", {})
            pave = data.get("pave", {})

            risk_flags = len(imsafe.get("risk_flags", []))
            env = str(pave.get("environment", ""))

            # Pattern: fatigue + bad weather type correlation
            if "fatigue" in str(imsafe).lower() and "weather" in env.lower():
                high_risk_triggers["fatigue_weather_combo"] += 1

            pattern_counts["total_cases"] += 1

        return {
            "total_logs": len(logs),
            "patterns": dict(pattern_counts),
            "risk_triggers": dict(high_risk_triggers)
        }

    # --------------------------------------------------------
    # Suggest adjustment factors
    # --------------------------------------------------------
    def calibration_factors(self):
        patterns = self.analyze_patterns()

        factors = {
            "likelihood_multiplier": 1.0,
            "severity_multiplier": 1.0
        }

        triggers = patterns.get("risk_triggers", {})

        # If fatigue + weather appears often → increase likelihood sensitivity
        if triggers.get("fatigue_weather_combo", 0) > 3:
            factors["likelihood_multiplier"] = 1.2

        return {
            "patterns": patterns,
            "factors": factors
        }