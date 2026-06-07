import re

SEVERITY_KEYWORDS = {
    "A": ["catastrophic", "catastrophe", "fatal", "multiple fatalities", "aircraft loss", "hull loss"],
    "B": ["hazardous", "serious incident", "serious injury", "near catastrophic", "major damage"],
    "C": ["major", "significant incident", "major incident", "significant injury", "major defect"],
    "D": ["minor", "minor incident", "minor injury", "slight damage", "no significant injury"],
    "E": ["negligible", "negligible incident", "no injury", "no damage", "inconsequential"],
}

LIKELIHOOD_KEYWORDS = {
    5: ["frequent", "frequently", "continuous", "daily", "multiple times", "often", "common"],
    4: ["occasional", "occasionally", "sometimes", "weekly", "monthly", "several times"],
    3: ["remote", "remotely", "unlikely but possible", "seldom", "few times", "rarely"],
    2: ["improbable", "very unlikely", "highly unlikely", "almost never", "extremely rare"],
    1: ["incredible", "extremely improbable", "practically impossible", "virtually impossible"],
}

SEVERITY_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
LIKELIHOOD_ORDER = {5: 0, 4: 1, 3: 2, 2: 3, 1: 4}

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

PRIORITY_MAP = {
    "intolerable": "immediate",
    "tolerable": "urgent",
    "acceptable": "routine",
}

REQUIRED_ACTION = {
    "intolerable": "Immediate grounding or mitigation before further operation",
    "tolerable": "Acceptable only with risk mitigation; management approval required",
    "acceptable": "Acceptable as-is; routine monitoring",
}


def _score_keywords(text: str, keyword_map: dict) -> tuple:
    text_lower = text.lower()
    best_key = None
    best_score = 0
    for key, words in keyword_map.items():
        score = 0
        for word in words:
            count = len(re.findall(re.escape(word), text_lower))
            score += count
        if score > best_score:
            best_score = score
            best_key = key
    return best_key, best_score


def calculate_risk_index(description: str) -> dict:
    severity, sev_score = _score_keywords(description, SEVERITY_KEYWORDS)
    likelihood, like_score = _score_keywords(description, LIKELIHOOD_KEYWORDS)

    if severity is None:
        severity = "C"
    if likelihood is None:
        likelihood = 3

    risk_index = f"{likelihood}{severity}"
    zone = RISK_ZONE_MATRIX.get((str(likelihood), severity), "acceptable")
    priority = PRIORITY_MAP[zone]

    return {
        "severity": severity,
        "severity_label": {
            "A": "Catastrophic", "B": "Hazardous", "C": "Major",
            "D": "Minor", "E": "Negligible",
        }[severity],
        "likelihood": likelihood,
        "likelihood_label": {
            5: "Frequent", 4: "Occasional", 3: "Remote",
            2: "Improbable", 1: "Extremely Improbable",
        }[likelihood],
        "risk_index": risk_index,
        "risk_zone": zone,
        "priority": priority,
        "required_action": REQUIRED_ACTION[zone],
        "severity_keyword_score": sev_score,
        "likelihood_keyword_score": like_score,
    }
