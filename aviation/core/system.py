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
from aviation.cache.response_cache import AssessmentCache


class AviationSafetySystem:

    def __init__(self):
        self.dispatcher = AviationDispatcher()
        self.dashboard = SafetyDashboard()
        self.cache = AssessmentCache()

    # -------------------------------
    # REAL-TIME DECISION ENGINE
    # -------------------------------
    def assess_flight(self, scenario: str):
        """
        Main operational safety evaluation endpoint with caching.
        """
        cached = self.cache.get(scenario)
        if cached:
            return cached

        result = self.dispatcher.run(scenario)
        self.cache.set(scenario, result)
        return result

    # -------------------------------
    # SAFETY INTELLIGENCE REPORT
    # -------------------------------
    def generate_safety_report(self):
        """
        Converts historical logs into intelligence output.
        """
        return self.dashboard.get_summary()

    # -------------------------------
    # FUTURE EXPANSION HOOK
    # -------------------------------
    def simulate_scenarios(self, scenarios: list):
        """
        Batch risk simulation with caching.
        """
        results = []

        for s in scenarios:
            cached = self.cache.get(s)
            if cached:
                results.append(cached)
            else:
                result = self.dispatcher.run(s)
                self.cache.set(s, result)
                results.append(result)

        return results