def evaluate_pave(text: str):
    """
    Simple extraction-based PAVE risk detection
    """

    text = text.lower()

    pilot_risks = []
    aircraft_risks = []
    environment_risks = []
    external_risks = []

    # PILOT
    if any(k in text for k in ["fatigue", "tired", "stress", "ill", "unwell"]):
        pilot_risks.append("Pilot condition degraded")

    # AIRCRAFT
    if any(k in text for k in ["engine", "failure", "system", "maintenance"]):
        aircraft_risks.append("Possible aircraft system concern")

    # ENVIRONMENT
    if any(k in text for k in ["weather", "storm", "wind", "visibility", "rain", "cloud"]):
        environment_risks.append("Adverse weather conditions")

    if "lukla" in text or "mountain" in text:
        environment_risks.append("High terrain risk environment")

    # EXTERNAL PRESSURE
    if any(k in text for k in ["delay", "schedule", "pressure", "time", "fuel"]):
        external_risks.append("Operational pressure present")

    return {
        "pilot": pilot_risks,
        "aircraft": aircraft_risks,
        "environment": environment_risks,
        "external": external_risks
    }