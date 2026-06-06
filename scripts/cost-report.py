#!/usr/bin/env python3
"""
Generate weekly OpenRouter cost report
"""

import json
from datetime import datetime, timedelta

HAIKU_COST_PER_1K = 0.002
SONNET_COST_PER_1K = 0.006


def generate_cost_report(log_entries: list = None):
    """Analyze API usage and costs from log entries"""
    if log_entries is None:
        log_entries = []

    total_calls = len(log_entries)
    total_tokens = sum(e.get("tokens", 0) for e in log_entries)
    haiku_calls = sum(1 for e in log_entries if e.get("model") == "claude-3-haiku-20240307")
    sonnet_calls = sum(1 for e in log_entries if e.get("model") == "claude-3-sonnet-20240229")

    haiku_cost = (haiku_calls * 500 / 1000) * HAIKU_COST_PER_1K
    sonnet_cost = (sonnet_calls * 500 / 1000) * SONNET_COST_PER_1K
    estimated_cost = round(haiku_cost + sonnet_cost, 4)

    sonnet_cost_if_haiku = (sonnet_calls * 500 / 1000) * HAIKU_COST_PER_1K
    cost_savings = round(sonnet_cost - sonnet_cost_if_haiku, 4)

    report = {
        "period": f"{(datetime.now() - timedelta(days=7)).date()} to {datetime.now().date()}",
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "haiku_calls": haiku_calls,
        "sonnet_calls": sonnet_calls,
        "estimated_cost_usd": estimated_cost,
        "cost_savings_via_smart_selection_usd": cost_savings,
        "recommendations": []
    }

    if total_calls > 1000:
        report["recommendations"].append("Consider stricter caching to reduce API calls")
    if estimated_cost > 10:
        report["recommendations"].append("Batch processing recommended to reduce cost")
    if sonnet_calls > haiku_calls * 2:
        report["recommendations"].append("Most scenarios use Sonnet — review complexity detection thresholds")
    if cost_savings > 5:
        report["recommendations"].append(f"Smart model selection saved ${cost_savings} — keep it enabled")

    return report


if __name__ == "__main__":
    sample_logs = [
        {"model": "claude-3-haiku-20240307", "tokens": 450},
        {"model": "claude-3-haiku-20240307", "tokens": 320},
        {"model": "claude-3-sonnet-20240229", "tokens": 680},
        {"model": "claude-3-haiku-20240307", "tokens": 410},
    ]
    report = generate_cost_report(sample_logs)
    print(json.dumps(report, indent=2))
