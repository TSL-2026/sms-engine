def evaluate_imsafe(input_text: str):
    """
    Simple rule-based IMSAFE risk hints.
    This will later feed dispatcher logic.
    """

    risk_flags = []

    keywords = {
        "fatigue": "Fatigue risk detected",
        "tired": "Fatigue risk detected",
        "stress": "Stress risk detected",
        "ill": "Illness risk detected",
        "medication": "Medication risk detected",
        "alcohol": "Alcohol risk detected",
    }

    for key, message in keywords.items():
        if key in input_text.lower():
            risk_flags.append(message)

    return {
        "risk_flags": risk_flags,
        "risk_level": "HIGH" if len(risk_flags) >= 2 else "LOW"
    }