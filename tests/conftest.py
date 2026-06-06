import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("OPENROUTER_API_KEY", "sk-test-key")


@pytest.fixture
def sample_low_risk_scenario():
    return "Pilot rested, VFR conditions, familiar airport, daytime"


@pytest.fixture
def sample_high_risk_scenario():
    return (
        "Pilot severely fatigued with 3 hours sleep, "
        "strong crosswinds, mountainous terrain, "
        "aircraft has known hydraulic leak, "
        "pressure from management to complete delivery"
    )


@pytest.fixture
def dispatcher():
    from aviation.dispatcher import AviationDispatcher
    return AviationDispatcher()
