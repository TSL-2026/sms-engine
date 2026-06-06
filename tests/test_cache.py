import pytest
from aviation.cache.response_cache import AssessmentCache


class TestAssessmentCache:
    def test_cache_miss(self):
        cache = AssessmentCache()
        result = cache.get("Pilot rested, VFR conditions")
        assert result is None

    def test_cache_hit(self):
        cache = AssessmentCache()
        data = {"decision": {"state": "CLEARED", "risk_score": 3}}

        cache.set("Pilot rested, VFR conditions", data)
        result = cache.get("Pilot rested, VFR conditions")
        assert result == data

    def test_cache_normalizes_input(self):
        cache = AssessmentCache()
        data = {"decision": {"state": "CLEARED"}}

        cache.set("Pilot rested, VFR conditions", data)
        result = cache.get("  PILOT RESTED,   vfr CONDITIONS  ")
        assert result == data

    def test_cache_clear(self):
        cache = AssessmentCache()
        cache.set("test scenario", {"score": 5})
        cache.clear()
        assert cache.get("test scenario") is None

    def test_different_scenarios_different_keys(self):
        cache = AssessmentCache()
        cache.set("Scenario A", {"result": "A"})
        cache.set("Scenario B", {"result": "B"})

        assert cache.get("Scenario A") == {"result": "A"}
        assert cache.get("Scenario B") == {"result": "B"}
