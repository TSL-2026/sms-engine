# ============================================================
# File: aviation/core/system.py
# Version: v2.0.0
#
# Module: Aviation Safety System Core
#
# Purpose:
#   Single entry point for entire aviation safety platform.
#   Replaces scripts like ai.py and test files.
# ============================================================

from aviation.dispatcher import AviationDispatcher
from aviation.analytics.safety_dashboard import SafetyDashboard


class AviationSafetySystem:

    def __init__(self):
        self.dispatcher = AviationDispatcher()
        self.dashboard = SafetyDashboard()

    # -------------------------------
    # REAL-TIME DECISION ENGINE
    # -------------------------------
    def assess_flight(self, scenario: str):
        """
        Main operational safety evaluation endpoint.
        """
        return self.dispatcher.run(scenario)

    # -------------------------------
    # SAFETY INTELLIGENCE REPORT
    # -------------------------------
    def generate_safety_report(self):
        """
        Converts historical logs into intelligence output.
        """
        return self.dashboard.generate_report()

    # -------------------------------
    # FUTURE EXPANSION HOOK
    # -------------------------------
    def simulate_scenarios(self, scenarios: list):
        """
        Batch risk simulation (future ML training dataset).
        """
        results = []

        for s in scenarios:
            results.append(self.dispatcher.run(s))

        return results