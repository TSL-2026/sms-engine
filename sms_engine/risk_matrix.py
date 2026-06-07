"""
Doc 9859 Risk Matrix Engine

Severity: A (Catastrophic) → E (Negligible)
Likelihood: 5 (Frequent) → 1 (Extremely Improbable)

Risk Index = Severity + Likelihood (e.g., "3B")
"""

SEVERITY_LABELS = {
    "A": "Catastrophic",
    "B": "Hazardous",
    "C": "Major",
    "D": "Minor",
    "E": "Negligible",
}

SEVERITY_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}

LIKELIHOOD_LABELS = {
    5: "Frequent",
    4: "Occasional",
    3: "Remote",
    2: "Improbable",
    1: "Extremely Improbable",
}

RISK_ZONE_MATRIX = {
    ("5", "A"): "intolerable",
    ("5", "B"): "intolerable",
    ("5", "C"): "intolerable",
    ("4", "A"): "intolerable",
    ("4", "B"): "intolerable",
    ("3", "A"): "intolerable",
    ("5", "D"): "tolerable",
    ("5", "E"): "tolerable",
    ("4", "C"): "tolerable",
    ("4", "D"): "tolerable",
    ("3", "B"): "tolerable",
    ("3", "C"): "tolerable",
    ("2", "A"): "tolerable",
    ("2", "B"): "tolerable",
    ("4", "E"): "acceptable",
    ("3", "D"): "acceptable",
    ("3", "E"): "acceptable",
    ("2", "C"): "acceptable",
    ("2", "D"): "acceptable",
    ("2", "E"): "acceptable",
    ("1", "A"): "acceptable",
    ("1", "B"): "acceptable",
    ("1", "C"): "acceptable",
    ("1", "D"): "acceptable",
    ("1", "E"): "acceptable",
}

RISK_INDEX_ORDER = [
    "5A", "5B", "5C", "4A", "4B", "3A",
    "5D", "4C", "4D", "3B", "3C", "2A", "2B",
    "4E", "3D", "3E", "2C", "2D", "2E", "1A", "1B", "1C", "1D", "1E",
]


def assess_risk(severity: str, likelihood: int) -> dict:
    severity = severity.upper()
    if severity not in SEVERITY_LABELS:
        raise ValueError(f"Invalid severity: {severity}. Must be A, B, C, D, or E")
    if likelihood not in LIKELIHOOD_LABELS:
        raise ValueError(f"Invalid likelihood: {likelihood}. Must be 1-5")

    risk_index = f"{likelihood}{severity}"
    zone = RISK_ZONE_MATRIX.get((str(likelihood), severity), "acceptable")

    required_action = {
        "intolerable": "Immediate grounding or mitigation before further operation",
        "tolerable": "Acceptable only with risk mitigation; management approval required",
        "acceptable": "Acceptable as-is; routine monitoring",
    }

    return {
        "severity": severity,
        "severity_label": SEVERITY_LABELS[severity],
        "likelihood": likelihood,
        "likelihood_label": LIKELIHOOD_LABELS[likelihood],
        "risk_index": risk_index,
        "risk_zone": zone,
        "required_action": required_action[zone],
    }


def get_matrix_table() -> list[list]:
    severities = ["A", "B", "C", "D", "E"]
    likelihoods = [5, 4, 3, 2, 1]
    rows = []
    for l in likelihoods:
        row = {"likelihood": l, "label": LIKELIHOOD_LABELS[l], "cells": []}
        for s in severities:
            entry = assess_risk(s, l)
            row["cells"].append(entry)
        rows.append(row)
    return rows
