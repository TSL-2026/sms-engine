"""
Seed script for AviaSafe SMS --- creates tenants, users, hazards,
risk assessments, reports (MOR/VSR), and CANs across all operators.

Run: python scripts/seed_data.py
"""

import json
import os
import random
from datetime import datetime, timezone, timedelta

SMS_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sms_db")
os.makedirs(SMS_DB, exist_ok=True)

NOW = datetime.now(timezone.utc)
YEAR = NOW.strftime("%Y")


def _id(prefix: str) -> str:
    return f"{prefix}_{NOW.strftime('%Y%m%d%H%M%S%f')}_{random.randint(100,999)}"


def write_json(filename: str, data: dict):
    path = os.path.join(SMS_DB, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def days_ago(d: int, hour: int = 12) -> str:
    return (NOW - timedelta(days=d, hours=random.randint(0, 6))).isoformat()


# -- Tenants --------------------------------------------------------------
TENANTS = [
    {"id": "caan",              "name": "Civil Aviation Authority of Nepal",  "code": "CAAN", "is_active": True, "type": "regulator"},
    {"id": "sita-air",          "name": "Sita Air",                          "code": "STA",  "is_active": True, "type": "operator", "base": "KTM", "fleet": "Dornier 228, Let L-410", "focus": "Domestic scheduled + cargo"},
    {"id": "buddha-air",        "name": "Buddha Air",                        "code": "BHA",  "is_active": True, "type": "operator", "base": "KTM", "fleet": "ATR 72, ATR 42",          "focus": "Domestic scheduled"},
    {"id": "yeti-airlines",     "name": "Yeti Airlines",                     "code": "NYT",  "is_active": True, "type": "operator", "base": "KTM", "fleet": "ATR 72, ATR 42",          "focus": "Domestic + STOL"},
    {"id": "shree-airlines",    "name": "Shree Airlines",                    "code": "SHA",  "is_active": True, "type": "operator", "base": "KTM", "fleet": "CRJ-200, Dash 8, Mi-17",   "focus": "Charter + Helicopter"},
    {"id": "nepal-airlines",    "name": "Nepal Airlines Corporation",        "code": "NAC",  "is_active": True, "type": "operator", "base": "KTM", "fleet": "A320, A330, ATR 42, Twin Otter", "focus": "International + Domestic"},
    {"id": "saurya-airlines",   "name": "Saurya Airlines",                   "code": "SAU",  "is_active": True, "type": "operator", "base": "KTM", "fleet": "CRJ-200",                "focus": "Domestic jet"},
    {"id": "summit-air",        "name": "Summit Air",                        "code": "SMA",  "is_active": True, "type": "operator", "base": "KTM", "fleet": "L-410, Dornier 228",      "focus": "STOL + Mountain"},
]

for t in TENANTS:
    write_json(f"tenants_{t['id']}.json", {**t, "created_at": days_ago(180)})

print(f"[OK] {len(TENANTS)} tenants seeded")

# -- Users ----------------------------------------------------------------
USERS = [
    # CAAN regulator users
    {"tenant_id": "caan",          "email": "regulator@caan.gov.np",    "name": "CAAN Regulator",       "role": "regulator",       "department": "Safety Oversight"},
    {"tenant_id": "caan",          "email": "safety@caan.gov.np",      "name": "Safety Director",      "role": "safety_officer",  "department": "Safety Oversight"},
    # Operator safety managers
    {"tenant_id": "sita-air",      "email": "safety@sitaair.com.np",   "name": "Sita Safety Manager",  "role": "safety_manager",  "department": "Safety"},
    {"tenant_id": "buddha-air",    "email": "safety@buddhaair.com",    "name": "Buddha Safety Mgr",    "role": "safety_manager",  "department": "Safety"},
    {"tenant_id": "yeti-airlines", "email": "safety@yeti.com.np",      "name": "Yeti Safety Mgr",      "role": "safety_manager",  "department": "Safety"},
    {"tenant_id": "shree-airlines","email": "safety@shreeair.com.np",  "name": "Shree Safety Mgr",     "role": "safety_manager",  "department": "Safety"},
    {"tenant_id": "nepal-airlines","email": "safety@nac.com.np",       "name": "NAC Safety Mgr",       "role": "safety_manager",  "department": "Safety"},
    {"tenant_id": "saurya-airlines","email": "safety@sauryaair.com.np","name": "Saurya Safety Mgr",    "role": "safety_manager",  "department": "Safety"},
    {"tenant_id": "summit-air",    "email": "safety@summitair.com.np", "name": "Summit Safety Mgr",    "role": "safety_manager",  "department": "Safety"},
]

for u in USERS:
    doc_id = _id("users")
    write_json(f"users_{doc_id}.json", {**u, "id": doc_id, "is_active": True, "created_at": days_ago(180)})

print(f"[OK] {len(USERS)} users seeded")

# -- Hazard definitions ---------------------------------------------------
# (tenant_id, title, description, category, severity, likelihood, status, days_old, closed_days_old)
HAZARD_DEFS = [
    # -- Sita Air (8 hazards mixing old+recent, open+closed) --
    ("sita-air", "Engine FOD on Dornier 228 Runway 02 KTM",
     "Foreign object debris ingested during taxi on Runway 02 at KTM. No damage reported but near-miss on departure.",
     "technical", "D", 2, "closed", 150, 120),
    ("sita-air", "Cargo hold door warning light inoperative",
     "Cargo door annunciator failed during pre-flight at KTM. Deferred per MEL but need permanent fix.",
     "technical", "D", 3, "closed", 130, 100),
    ("sita-air", "Bird strike hazard near KTM approach --- increasing frequency",
     "Three bird strike near-misses reported in last 60 days on approach to KTM RWY 02. Wildlife management inadequate.",
     "environmental", "C", 4, "open", 30, None),
    ("sita-air", "Pilot fatigue reported on double-daily KTM-BHR rotation",
     "Crew reported fatigue after second sector on KTM-BHR-KTM. Duty day exceeded 12 hours with delays.",
     "organizational", "B", 3, "open", 15, None),
    ("sita-air", "Runway excursion during wet landing at BHR",
     "Aircraft veered left on wet runway during landing at Bharatpur. No injuries. Runway friction below threshold.",
     "operational", "C", 3, "under_mitigation", 90, None),
    ("sita-air", "Missing tool in AMO hangar --- potential FOD",
     "Torque wrench unaccounted for after C-check on 9N-ALP. Search conducted. Tool later found in engine bay.",
     "technical", "D", 2, "closed", 200, 185),
    ("sita-air", "GPS interference on KTM-JMO route --- recurring",
     "GPS signal loss reported on 4 flights on same route in March. Possible jamming or antenna issue.",
     "technical", "C", 3, "open", 45, None),
    ("sita-air", "STOL approach instability at Lukla --- increasing trend",
     "Two unstabilized approaches at VNLK in last month. Windshear and gusty conditions. Go-around executed.",
     "operational", "B", 4, "under_mitigation", 25, None),

    # -- Buddha Air (8 hazards) --
    ("buddha-air", "ATR 72 flap asymmetry indication --- recurrent",
     "Recurrent flap asymmetry ECAM warnings on 9N-AKM. Resetting temporarily clears but root cause not found.",
     "technical", "C", 3, "open", 40, None),
    ("buddha-air", "Runway incursion at KTM --- vehicle on active",
     "Ground vehicle crossed runway 02 during ATR landing roll. Aerodrome vehicle procedure not followed.",
     "operational", "B", 3, "under_mitigation", 60, None),
    ("buddha-air", "Mountain weather misforecast --- missed approach at PPL",
     "Forecast called for VMC but encountered IMC at Pokhara. Missed approach executed. Need better briefing.",
     "environmental", "C", 2, "closed", 110, 90),
    ("buddha-air", "Cabin crew oxygen bottle found expired",
     "Three oxygen bottles in cabin exceeded hydrostatic test date. Maintenance scheduling gap identified.",
     "technical", "D", 3, "closed", 170, 155),
    ("buddha-air", "Ground damage to ATR winglet during pushback",
     "Winglet contacted boarding stairs at KTM stand 4. Marshalling procedure not followed. Damage repairable.",
     "operational", "D", 2, "open", 20, None),
    ("buddha-air", "VHF comm failure on KTM-SIF sector",
     "Loss of radio contact for 8 minutes. Aircraft established on backup. Investigation shows antenna corrosion.",
     "technical", "C", 3, "open", 55, None),
    ("buddha-air", "Fuel contamination found in sump sample --- KTM base",
     "Water and sediment found in main tank sump sample during daily inspection. Refueling source suspected.",
     "technical", "B", 2, "closed", 190, 175),
    ("buddha-air", "GPWS alert on approach to VNSB --- terrain clearance marginal",
     "GPWS 'PULL UP' at 1200ft AGL on approach to Simara. Deviation from published procedure. Crew retrained.",
     "operational", "A", 3, "under_mitigation", 80, None),

    # -- Yeti Airlines (7 hazards) --
    ("yeti-airlines", "ATR 42 autopilot disengagement anomaly",
     "Autopilot unexpectedly disengaged at FL180 on KTM-BDP sector. Crew re-engaged and continued. Logs show servo fault.",
     "technical", "C", 3, "under_mitigation", 50, None),
    ("yeti-airlines", "Baggage loading discrepancy --- weight and balance error",
     "Loading manifest incorrect by 350kg. Discrepancy found during final fuel calculation. Departure delayed.",
     "organizational", "C", 3, "open", 35, None),
    ("yeti-airlines", "Wake turbulence encounter on approach KTM",
     "Moderate wake turbulence behind A330 on approach. No injuries. Separation inadequate.",
     "operational", "C", 2, "closed", 120, 105),
    ("yeti-airlines", "Crew duty time breach due to MRO delays",
     "Maintenance overran by 3 hours causing crew to exceed duty limits. Regulation 6.6 hours exceeded by 45 min.",
     "organizational", "B", 4, "open", 10, None),
    ("yeti-airlines", "APU fire warning false activation",
     "APU fire warning triggered on ground. Cabin evacuated. False alarm --- sensor contamination. Recurring on 9N-ANO.",
     "technical", "D", 3, "open", 70, None),
    ("yeti-airlines", "Lukla landing distance exceedance on wet runway",
     "Landing distance exceeded available runway length at VNLK by estimated 30m. Wet conditions. Risk review opened.",
     "operational", "B", 4, "under_mitigation", 18, None),
    ("yeti-airlines", "Security --- unauthorized person accessed apron at KTM",
     "Individual accessed apron via cargo gate. No escort. Security patrol detained. Breach report filed.",
     "organizational", "D", 2, "closed", 140, 125),

    # -- Shree Airlines (6 hazards) --
    ("shree-airlines", "CRJ-200 engine stall warning on climb-out",
     "Compressor stall at FL220. Power reduced, recovered. Boroscope inspection planned. Fleet-wide bulletin expected.",
     "technical", "A", 3, "open", 12, None),
    ("shree-airlines", "Dash 8 nose gear steering failure",
     "Nose wheel steering unresponsive after landing at KTM. Towed to stand. Hydraulic leak in steering actuator.",
     "technical", "C", 2, "closed", 160, 145),
    ("shree-airlines", "Charter helipad misidentified at remote village",
     "Helicopter landed at wrong LZ. Sites unmarked. Passenger confusion. Procedure for remote LZ verification needed.",
     "operational", "D", 3, "open", 85, None),
    ("shree-airlines", "Bird activity at KTM --- increased hazard for CRJ ops",
     "Multiple bird sightings on RWY 02 during CRJ operations. 6 near-misses reported in 2 months.",
     "environmental", "C", 4, "open", 22, None),
    ("shree-airlines", "Mi-17 cargo hook failure during sling operation",
     "Cargo hook released prematurely at 50ft. Load dropped safely in unpopulated area. Annual inspection findings.",
     "technical", "A", 2, "under_mitigation", 75, None),
    ("shree-airlines", "Fuel uplift discrepancy at KTM --- wrong grade",
     "Jet A1 instead of Jet A provided on one operation. Detected before fueling. Supplier procedure review.",
     "organizational", "C", 2, "closed", 100, 90),

    # -- Nepal Airlines (7 hazards) --
    ("nepal-airlines", "A320 tail strike on landing at KTM",
     "Tail contacted runway on landing. Inspection found structural damage. AOG for 5 days.",
     "technical", "B", 3, "closed", 200, 180),
    ("nepal-airlines", "Foreign object on KTM RWY 02 --- A320 rejected takeoff",
     "RTO at 80 knots due to debris on runway. Tires inspected. Debris traced to construction works near threshold.",
     "operational", "C", 3, "open", 28, None),
    ("nepal-airlines", "ATC communication language proficiency concern",
     "Pilot and ATC language barrier on international flight. Potential misunderstanding on altitude assignment.",
     "organizational", "C", 2, "closed", 110, 95),
    ("nepal-airlines", "A330 engine vibration on long-haul --- KTM-DOH",
     "N1 vibration above limits at cruise. Engine parameter stabilized. Return decided. Fan blade inspection needed.",
     "technical", "B", 3, "open", 42, None),
    ("nepal-airlines", "Twin Otter cabin door seal failed at altitude",
     "Cabin pressure loss at FL100. Door seal deteriorated. Aircraft descended to 8000 ft. Oxygen not needed.",
     "technical", "D", 3, "open", 65, None),
    ("nepal-airlines", "IFR approach minima deviation at KTM in monsoon",
     "Crew descended below minima inadvertently during monsoon approach. GPWS 'MINIMUMS' alerted.",
     "operational", "B", 4, "under_mitigation", 14, None),
    ("nepal-airlines", "Wildlife strike on ATR departure --- multiple birds",
     "Multiple bird strikes on climb-out. Engine parameters normal. Visual inspection post-flight. No damage.",
     "environmental", "C", 3, "open", 8, None),

    # -- Saurya Airlines (5 hazards) --
    ("saurya-airlines", "CRJ-200 brake temperature exceedance",
     "Brake temperature exceeded 300°C after landing. Parked for cooling per AMM. Investigation shows worn brakes.",
     "technical", "D", 3, "open", 48, None),
    ("saurya-airlines", "Crew scheduling system error --- double booking",
     "Two captains assigned to same flight. Manual override required. Scheduling system migration caused issues.",
     "organizational", "C", 3, "closed", 90, 75),
    ("saurya-airlines", "Repeated missed approaches at KTM in haze",
     "3 missed approaches in one day due to visibility below CAT I minima at KTM. Procedure review opened.",
     "operational", "C", 4, "open", 5, None),
    ("saurya-airlines", "Oxygen mask stowage compliance in cabin",
     "15% of passenger oxygen masks found improperly stowed. Cabin crew checks not catching it.",
     "organizational", "D", 2, "closed", 135, 120),
    ("saurya-airlines", "TCAS RA on approach KTM --- A320 opposite direction",
     "TCAS resolution advisory on approach. Opposite direction traffic not announced by ATC. Near mid-air.",
     "operational", "A", 2, "under_mitigation", 55, None),

    # -- Summit Air (6 hazards) --
    ("summit-air", "L-410 landing gear abnormal retraction",
     "Left main gear retracted slowly on climb-out. Cycle time exceeded. Gear pinned for return landing.",
     "technical", "C", 2, "closed", 145, 130),
    ("summit-air", "Dornier 228 STOL performance below chart in high DA",
     "At Lukla (DA ~11,000ft), climb gradient below published. Load reduction required. Chart review initiated.",
     "operational", "B", 3, "open", 38, None),
    ("summit-air", "Cargo restraint failure on Dornier 228",
     "Cargo shifted in flight on KTM-TCR sector. No injury. Load securement procedure not compliant.",
     "operational", "D", 3, "open", 60, None),
    ("summit-air", "Windshear at Simikota --- go-around executed",
     "Loss of 25 kts at 200ft AGL on final. Go-around called. Windshear escape maneuver performed. Heightened risk on STOL.",
     "environmental", "B", 4, "open", 7, None),
    ("summit-air", "Pilot incapacitation suspect --- food poisoning",
     "Pilot reported ill before second sector. Replacement crew called. Fatigue/illness reporting culture concern.",
     "organizational", "C", 3, "under_mitigation", 32, None),
    ("summit-air", "De-icing fluid stockout at KTM during cold snap",
     "Type I fluid exhausted during morning operation. Two departures delayed. Supplier lead time issue flagged.",
     "organizational", "D", 3, "closed", 80, 70),

    # -- Cross-operator systemic hazards (for leading indicator detection) --
    ("sita-air", "STOL hazard --- bird activity at Lukla increasing",
     "Bird activity around VNLK increased by 40% this quarter. Multiple near-misses. Risk of engine ingestion.",
     "environmental", "B", 4, "open", 20, None),
    ("buddha-air", "STOL hazard --- bird activity at Pokhara increasing",
     "VNPK bird presence up 60% since last year. Weekly near-miss reports. Local waste management issue.",
     "environmental", "B", 4, "open", 18, None),
    ("yeti-airlines", "STOL hazard --- runway condition at Lukla degraded",
     "VNLK runway friction measured below recommended. Surface maintenance deferred. Wet performance critical.",
     "operational", "B", 4, "open", 12, None),
    ("summit-air", "STOL hazard --- approach lighting at Simikota intermittent",
     "PAPI lights unreliable at VNSK. NOTAM issued. Night operations restricted until repair.",
     "technical", "C", 3, "open", 25, None),
    ("sita-air", "Runway incursion KTM --- increasing trend across operators",
     "3 incursions in 60 days across multiple operators. Apron vehicle procedures widely non-compliant.",
     "operational", "B", 3, "under_mitigation", 35, None),
    ("nepal-airlines", "GPWS alert trend on KTM approach --- monsoon season",
     "4 GPWS alerts in June on same approach. Monsoon weather + terrain combination high risk.",
     "operational", "B", 3, "open", 9, None),
    ("shree-airlines", "Maintenance documentation gaps --- multiple findings",
     "Repeat audit findings across 3 operators on maintenance documentation. Systemic training gap.",
     "organizational", "C", 3, "open", 30, None),
    ("saurya-airlines", "Fuel quality reporting gap --- no centralized system",
     "Operators not reporting fuel quality data to regulator. Potential contamination chain unidentified.",
     "organizational", "C", 3, "open", 40, None),
]

def assess(severity: str, likelihood: int) -> dict:
    SEV_MAP = {"A": "Catastrophic", "B": "Hazardous", "C": "Major", "D": "Minor", "E": "Negligible"}
    LIK_MAP = {5: "Frequent", 4: "Occasional", 3: "Remote", 2: "Improbable", 1: "Extremely Improbable"}
    ZONES = {
        ("5","A"): "intolerable", ("5","B"): "intolerable", ("5","C"): "intolerable",
        ("4","A"): "intolerable", ("4","B"): "intolerable", ("3","A"): "intolerable",
        ("5","D"): "tolerable",   ("5","E"): "tolerable",   ("4","C"): "tolerable",
        ("4","D"): "tolerable",   ("3","B"): "tolerable",   ("3","C"): "tolerable",
        ("2","A"): "tolerable",   ("2","B"): "tolerable",
        ("4","E"): "acceptable",  ("3","D"): "acceptable",  ("3","E"): "acceptable",
        ("2","C"): "acceptable",  ("2","D"): "acceptable",  ("2","E"): "acceptable",
        ("1","A"): "acceptable",  ("1","B"): "acceptable",  ("1","C"): "acceptable",
        ("1","D"): "acceptable",  ("1","E"): "acceptable",
    }
    zone = ZONES.get((str(likelihood), severity), "acceptable")
    risk_index = f"{likelihood}{severity}"
    return {
        "severity": severity, "severity_label": SEV_MAP[severity],
        "likelihood": likelihood, "likelihood_label": LIK_MAP[likelihood],
        "risk_index": risk_index, "risk_zone": zone,
    }

hazard_count = 0
risk_count = 0

for i, (tid, title, desc, cat, sev, lik, status, days_old, closed_days) in enumerate(HAZARD_DEFS, start=1):
    hid = f"HR-{YEAR}-{i:04d}"
    created_at = days_ago(days_old)

    hazard = {
        "tenant_id": tid,
        "hazard_id": hid,
        "title": title,
        "description": desc,
        "category": cat,
        "source_report_ids": [],
        "status": status,
        "created_by": f"{tid.split('-')[0]}-safety",
        "created_at": created_at,
    }

    if status == "closed" and closed_days:
        hazard["closed_at"] = days_ago(closed_days)

    doc_id = _id("hazards")
    hazard["id"] = doc_id
    write_json(f"hazards_{doc_id}.json", hazard)

    r = assess(sev, lik)
    assessment = {
        "hazard_id": doc_id,
        "assessed_by": hazard["created_by"],
        "severity": r["severity"],
        "severity_label": r["severity_label"],
        "likelihood": r["likelihood"],
        "likelihood_label": r["likelihood_label"],
        "risk_index": r["risk_index"],
        "risk_zone": r["risk_zone"],
        "rationale": f"Assessed based on description (severity={r['severity_label']}, likelihood={r['likelihood_label']})",
        "assessed_at": created_at,
    }
    assess_id = _id("risk_assessments")
    assessment["id"] = assess_id
    write_json(f"risk_assessments_{assess_id}.json", assessment)

    hazard_count += 1
    risk_count += 1

print(f"[OK] {hazard_count} hazards seeded")
print(f"[OK] {risk_count} risk assessments seeded")

# -- Reports (MOR + VSR) --------------------------------------------------
REPORT_DEFS = [
    # (tenant_id, report_type, description, severity, days_old, linked_to_hazard)
    ("sita-air", "MOR", "Engine FOD ingestion near-miss during taxi at KTM", "C", 150, True),
    ("sita-air", "MOR", "Cargo hold door warning light failure inoperative per MEL", "D", 130, True),
    ("sita-air", "VSR", "Bird strike near-miss on approach KTM RWY 02 --- third this quarter", "C", 30, True),
    ("sita-air", "VSR", "Fatigue report after double daily KTM-BHR rotation", "B", 15, True),
    ("sita-air", "MOR", "Runway excursion at BHR during wet landing conditions", "C", 90, True),
    ("sita-air", "VSR", "GPS signal loss on KTM-JMO route --- possible jamming", "C", 45, True),
    ("sita-air", "VSR", "Unstabilized approach at Lukla --- windshear encountered", "B", 25, True),
    ("sita-air", "VSR", "Torque wrench lost during C-check --- potential FOD hazard", "D", 200, True),
    ("sita-air", "VSR", "Aircraft towing incident at KTM ground handling", "D", 95, False),
    ("sita-air", "MOR", "Bird ingestion by Dornier on departure from KTM", "C", 50, False),

    ("buddha-air", "MOR", "Flap asymmetry ECAM warning on ATR 72 --- recurrent", "C", 40, True),
    ("buddha-air", "MOR", "Vehicle incursion on active runway during ATR landing", "B", 60, True),
    ("buddha-air", "VSR", "Missed approach at Pokhara --- actual weather below forecast", "C", 110, True),
    ("buddha-air", "VSR", "Expired oxygen bottles found in cabin --- scheduling gap", "D", 170, True),
    ("buddha-air", "MOR", "ATR winglet damaged during pushback at KTM", "D", 20, True),
    ("buddha-air", "VSR", "VHF comm loss on KTM-SIF sector --- antenna corrosion found", "C", 55, True),
    ("buddha-air", "VSR", "Fuel contamination in sump sample --- KTM refueler suspected", "B", 190, True),
    ("buddha-air", "MOR", "GPWS alert at Simara --- terrain clearance marginal on approach", "A", 80, True),

    ("yeti-airlines", "MOR", "Autopilot disengagement anomaly on ATR 42", "C", 50, True),
    ("yeti-airlines", "VSR", "Weight and balance error --- loading manifest wrong by 350kg", "C", 35, True),
    ("yeti-airlines", "VSR", "Wake turbulence encounter on approach KTM behind A330", "C", 120, True),
    ("yeti-airlines", "MOR", "Crew duty time exceedance due to maintenance overrun", "B", 10, True),
    ("yeti-airlines", "VSR", "APU fire warning false alarm --- sensor contamination", "D", 70, True),
    ("yeti-airlines", "MOR", "Lukla landing distance exceedance --- wet conditions", "B", 18, True),
    ("yeti-airlines", "VSR", "Unauthorized apron access at KTM via cargo gate", "D", 140, True),

    ("shree-airlines", "MOR", "CRJ-200 compressor stall on climb-out at FL220", "A", 12, True),
    ("shree-airlines", "VSR", "Nose gear steering failure on Dash 8 after landing", "C", 160, True),
    ("shree-airlines", "VSR", "Helipad misidentified at remote village by helicopter", "D", 85, True),
    ("shree-airlines", "VSR", "Bird activity at KTM --- 6 near-misses in 2 months on CRJ", "C", 22, True),
    ("shree-airlines", "MOR", "Mi-17 cargo hook premature release during sling operation", "A", 75, True),
    ("shree-airlines", "VSR", "Wrong fuel grade supplied --- detected before fueling", "C", 100, True),

    ("nepal-airlines", "MOR", "A320 tail strike on landing at KTM --- structural damage", "B", 200, True),
    ("nepal-airlines", "MOR", "Rejected takeoff at 80 kts due to FOD on KTM runway", "C", 28, True),
    ("nepal-airlines", "VSR", "ATC language barrier incident with international flight", "C", 110, True),
    ("nepal-airlines", "VSR", "A330 engine vibration at cruise on KTM-DOH sector", "B", 42, True),
    ("nepal-airlines", "VSR", "Cabin pressure loss on Twin Otter at FL100 --- door seal failure", "D", 65, True),
    ("nepal-airlines", "MOR", "IFR approach minima deviation at KTM during monsoon", "B", 14, True),
    ("nepal-airlines", "VSR", "Multiple bird strikes on ATR departure --- no damage", "C", 8, True),
    ("nepal-airlines", "VSR", "Taxiway lighting out at KTM --- night ops risk", "D", 3, False),

    ("saurya-airlines", "VSR", "CRJ-200 brake temperature exceeds 300°C after landing", "D", 48, True),
    ("saurya-airlines", "VSR", "Crew scheduling double-booking error", "C", 90, True),
    ("saurya-airlines", "VSR", "Three missed approaches at KTM in haze --- CAVOK below minima", "C", 5, True),
    ("saurya-airlines", "VSR", "Passenger oxygen mask stowage non-compliant --- 15% found loose", "D", 135, True),
    ("saurya-airlines", "MOR", "TCAS RA on approach KTM --- opposite direction traffic", "A", 55, True),

    ("summit-air", "VSR", "L-410 landing gear retraction slow --- cycle time exceeded", "C", 145, True),
    ("summit-air", "VSR", "STOL climb gradient below chart at Lukla high DA", "B", 38, True),
    ("summit-air", "VSR", "Cargo shift in flight on Dornier 228 --- load restraint non-compliant", "D", 60, True),
    ("summit-air", "MOR", "Severe windshear at Simikota --- go-around from 200ft", "B", 7, True),
    ("summit-air", "VSR", "Pilot incapacitation due to food poisoning --- replacement called", "C", 32, True),
    ("summit-air", "VSR", "De-icing fluid stockout at KTM during cold snap", "D", 80, True),
    ("summit-air", "MOR", "Engine failure on Dornier 228 on climb --- precautionary return", "C", 180, False),

    # Recent high-profile MORs for lagging indicator demonstration
    ("sita-air", "MOR", "STOL approach instability at Lukla --- go-around due to windshear", "B", 25, False),
    ("yeti-airlines", "MOR", "Bird ingestion ATR at KTM --- engine surge", "C", 22, False),
    ("buddha-air", "MOR", "Runway excursion ATR at Pokhara --- wet runway overrun", "B", 16, False),
    ("nepal-airlines", "MOR", "A320 engine surge on climb from KTM --- returned", "A", 11, False),
]

report_count = 0
hazard_docs = []
for fname in os.listdir(SMS_DB):
    if fname.startswith("hazards_") and fname.endswith(".json"):
        with open(os.path.join(SMS_DB, fname)) as f:
            hazard_docs.append(json.load(f))

hazard_by_tenant = {t["id"]: [] for t in TENANTS}
for h in hazard_docs:
    hazard_by_tenant.setdefault(h.get("tenant_id", ""), []).append(h)

# Build lookup for reports that should link to hazard by tenant + matching title
hazard_lookup = {}
for h in hazard_docs:
    key = (h["tenant_id"], h["title"][:30])
    hazard_lookup[key] = h["id"]

report_counter = 0
for (tid, rtype, rdesc, rsev, rold, link_to_hazard) in REPORT_DEFS:
    created = days_ago(rold)
    report = {
        "tenant_id": tid,
        "report_type": rtype,
        "status": random.choices(["submitted", "under_review", "triaged", "escalated_to_hazard", "closed"], weights=[30, 20, 10, 25, 15])[0],
        "submitted_by": f"reporter-{tid}-{random.randint(1,3)}",
        "occurrence_date": days_ago(rold + random.randint(0, 3)),
        "location": random.choice(["KTM", "VNLK", "VNPK", "VNSB", "VNBP", "VNKT"]),
        "description": rdesc,
        "initial_severity": rsev,
        "confidentiality": rtype == "VSR",
        "created_at": created,
    }

    if link_to_hazard:
        key = (tid, rdesc[:30])
        if key in hazard_lookup:
            report["hazard_id"] = hazard_lookup[key]
            report["status"] = "escalated_to_hazard"

    doc_id = _id("reports")
    report["id"] = doc_id
    write_json(f"reports_{doc_id}.json", report)
    report_count += 1

print(f"[OK] {report_count} reports seeded")

# -- CANs -----------------------------------------------------------------
PRIORITY_MAP = {"immediate": "High", "urgent": "High", "routine": "Medium"}
STATUS_MAP = {"open": "Issued", "under_mitigation": "Issued", "closed": "Accepted"}

CAN_DEFS = [
    ("sita-air", "Ground handling retraining for KTM marshallers",
     "Retrain all KTM ground handling staff on marshalling procedures. Install wing walker cameras.",
     "urgent", "open", 60),
    ("sita-air", "FOD prevention program --- runway sweeps",
     "Implement daily runway FOD sweeps at KTM and BHR. Acquire FOD detection vehicle.",
     "urgent", "open", 30),
    ("buddha-air", "ATR flap system deep inspection",
     "Deep inspection of flap system on 9N-AKM following recurrent asymmetry. Airbus bulletin compliance.",
     "urgent", "under_mitigation", 75),
    ("buddha-air", "Aerodrome vehicle procedure review",
     "Review and reinforce vehicle movement procedures on active runways. Install vehicle barrier system.",
     "immediate", "open", 14),
    ("yeti-airlines", "Crew scheduling system audit",
     "Full audit of crew scheduling system. Implement hard duty-time caps in software.",
     "urgent", "open", 45),
    ("yeti-airlines", "Wet runway landing procedure amendment",
     "Amend STOL landing distance calculations for wet conditions at Lukla. Increased safety margins.",
     "immediate", "open", 21),
    ("shree-airlines", "CRJ-200 engine trend monitoring",
     "Implement daily engine parameter monitoring on CRJ-200 fleet following compressor stall event.",
     "urgent", "open", 35),
    ("nepal-airlines", "KTM runway FOD control plan",
     "Coordinate with airport authority for construction debris control near RWY 02 threshold.",
     "urgent", "open", 40),
    ("nepal-airlines", "A330 fan blade inspection program",
     "Schedule NDT inspection of fan blades on A330 engine following vibration event.",
     "routine", "open", 60),
    ("saurya-airlines", "TCAS RA procedure review with ATC",
     "Safety meeting with KTM ATC on opposite-direction traffic procedures. Implement CRM training.",
     "immediate", "open", 28),
    ("summit-air", "STOL performance chart review",
     "Review and update STOL performance charts for L-410 and Dornier 228 at high-DA airfields.",
     "routine", "open", 90),
    ("nepal-airlines", "Monsoon approach minima review",
     "Safety bulletin to all flight crew on strict adherence to approach minima during monsoon.",
     "urgent", "under_mitigation", 45),
    ("buddha-air", "ATR wing walker procedure installation",
     "Install mandatory wing walker procedure for all ATR pushback operations at KTM.",
     "routine", "open", 60),
    ("yeti-airlines", "Security patrol compliance audit",
     "Quarterly audit of apron security patrols. Install additional access control cameras.",
     "routine", "open", 120),
    ("sita-air", "STOL approach procedure at Lukla",
     "Implement stabilized approach criteria specific to VNLK. Wind shear training for all STOL pilots.",
     "immediate", "open", 14),
    ("nepal-airlines", "ATC language proficiency program",
     "Coordinate language proficiency training for international operations. English proficiency testing.",
     "routine", "closed", 110),
    ("shree-airlines", "Helipad marking standardization",
     "Standardize helipad markings across all remote village LZs. GPS waypoint verification required.",
     "routine", "open", 75),
    ("saurya-airlines", "Oxygen mask stowage audit program",
     "Monthly oxygen mask compliance checks. Cabin crew training on proper stowage.",
     "routine", "closed", 135),
]

can_count = 0
for i, (tid, title, desc, priority, status, due_days) in enumerate(CAN_DEFS, start=1):
    can_id = f"CAN-{YEAR}-{i:04d}"
    created_at = days_ago(due_days + random.randint(5, 15))

    can = {
        "tenant_id": tid,
        "hazard_id": "",
        "can_id": can_id,
        "issued_by": f"regulator-{tid}-safety",
        "department_assigned": random.choice(["Safety", "Operations", "Maintenance", "Ground Handling", "Training"]),
        "due_date": days_ago(due_days),
        "priority": PRIORITY_MAP.get(priority, "Medium"),
        "description": desc,
        "status": STATUS_MAP.get(status, "Issued"),
        "issued_date": created_at,
        "created_at": created_at,
        "updated_at": created_at,
    }

    doc_id = _id("cans")
    can["id"] = doc_id
    write_json(f"cans_{doc_id}.json", can)
    can_count += 1

print(f"[OK] {can_count} corrective action notices seeded")

# -- CAPs -----------------------------------------------------------------
CAP_DEFS = [
    ("sita-air", "Ground handling FOD prevention and marshalling program",
     "Retrain all KTM ground handlers, install cameras, daily FOD sweeps",
     [{"action": "Retrain 25 ground staff on marshalling procedures", "owner": "Ground Ops Mgr", "target_date": "30 days", "status": "completed"},
      {"action": "Install wing walker cameras on all stands", "owner": "Engineering Mgr", "target_date": "60 days", "status": "in_progress"},
      {"action": "Procure FOD detection vehicle", "owner": "Procurement", "target_date": "90 days", "status": "pending"}],
     "FOD detection vehicle, camera system, training materials", "90 days", "Completed"),
    ("buddha-air", "ATR flap system inspection and ATC vehicle procedure",
     "Deep inspection of flap system, vehicle barrier installation",
     [{"action": "Complete AMM flap system inspection on 9N-AKM", "owner": "Maintenance Mgr", "target_date": "14 days", "status": "completed"},
      {"action": "Submit report to Airbus engineering", "owner": "Engineering Mgr", "target_date": "21 days", "status": "completed"},
      {"action": "Install vehicle barrier at RWY 02 holding point", "owner": "Airport Ops", "target_date": "45 days", "status": "in_progress"}],
     "Special tooling for flap actuator", "45 days", "Submitted"),
    ("yeti-airlines", "Crew scheduling system fix and STOL procedure update",
     "Implement hard duty-time caps, revise wet runway procedures",
     [{"action": "Full audit of crew scheduling system", "owner": "IT Mgr", "target_date": "30 days", "status": "in_progress"},
      {"action": "Implement hard duty-time limit in scheduling software", "owner": "IT Mgr", "target_date": "60 days", "status": "pending"},
      {"action": "Amend STOL landing distance for wet VNLK runway", "owner": "Chief Pilot", "target_date": "14 days", "status": "completed"}],
     "Software vendor contract, training", "60 days", "Approved"),
    ("shree-airlines", "CRJ-200 engine monitoring and helipad safety",
     "Daily engine checks, helipad marking standardization",
     [{"action": "Implement daily engine trend monitoring on CRJ-200 fleet", "owner": "Technical Mgr", "target_date": "14 days", "status": "completed"},
      {"action": "Create helipad marking standard for all remote LZs", "owner": "Safety Mgr", "target_date": "60 days", "status": "pending"}],
     "Engine monitoring software", "60 days", "InProgress"),
    ("nepal-airlines", "KTM FOD control and approach discipline",
     "Runway FOD control, monsoon approach minima compliance",
     [{"action": "Coordinate with airport for RWY 02 construction debris control", "owner": "Safety Mgr", "target_date": "30 days", "status": "in_progress"},
      {"action": "Issue safety bulletin on monsoon approach minima", "owner": "Chief Pilot", "target_date": "7 days", "status": "completed"}],
     "Airport coordination meeting", "30 days", "Submitted"),
    ("saurya-airlines", "TCAS RA procedure and oxygen compliance",
     "ATC communication procedure review, oxygen mask stowage program",
     [{"action": "Safety meeting with KTM ATC on opposite-direction traffic", "owner": "Safety Mgr", "target_date": "14 days", "status": "completed"},
      {"action": "Implement monthly oxygen mask compliance audits", "owner": "Cabin Crew Mgr", "target_date": "30 days", "status": "completed"},
      {"action": "CRM training for all flight crew", "owner": "Training Mgr", "target_date": "60 days", "status": "completed"}],
     "Training materials", "60 days", "Completed"),
    ("summit-air", "STOL performance review and cargo restraint fix",
     "High-DA performance charts update, cargo load training",
     [{"action": "Review and update STOL charts for L-410 at high-DA fields", "owner": "Chief Pilot", "target_date": "45 days", "status": "in_progress"},
      {"action": "Re-train loadmasters on Dornier 228 cargo restraint", "owner": "Ground Ops Mgr", "target_date": "30 days", "status": "pending"}],
     "Performance engineering consultation", "45 days", "Draft"),
]

can_count = 0
cap_count = 0
for fname in os.listdir(SMS_DB):
    if fname.startswith("cans_") and fname.endswith(".json"):
        can_count += 1

# Map CANs to CAPs by tenant
can_by_tenant = {}
for fname in os.listdir(SMS_DB):
    if fname.startswith("cans_") and fname.endswith(".json"):
        with open(os.path.join(SMS_DB, fname)) as f:
            c = json.load(f)
        can_by_tenant.setdefault(c.get("tenant_id", ""), []).append(c["id"])

for i, (tid, title, desc, items, resources, timeline, status) in enumerate(CAP_DEFS, start=1):
    can_ids = can_by_tenant.get(tid, [])
    if not can_ids:
        continue
    cap_id = f"CAP-{YEAR}-{i:04d}"
    created_at = days_ago(random.randint(30, 60))

    cap = {
        "tenant_id": tid,
        "can_id": can_ids[i % len(can_ids)],
        "cap_id": cap_id,
        "submitted_by": f"{tid.split('-')[0]}-safety",
        "submitted_date": created_at,
        "action_items": items,
        "resource_requirements": resources,
        "proposed_timeline": timeline,
        "status": status,
        "created_at": created_at,
        "updated_at": created_at,
    }

    if status == "Completed":
        cap["completed_date"] = days_ago(random.randint(1, 10))
        cap["approved_by"] = "caan-regulator"
        cap["approved_date"] = days_ago(random.randint(11, 20))
    elif status == "Approved":
        cap["approved_by"] = "caan-regulator"
        cap["approved_date"] = days_ago(random.randint(5, 15))
    elif status == "Rejected":
        cap["rejection_reason"] = "Insufficient detail in action items. Please revise and resubmit."
        cap["approved_by"] = "caan-regulator"

    doc_id = _id("caps")
    cap["id"] = doc_id
    write_json(f"caps_{doc_id}.json", cap)
    cap_count += 1

print(f"[OK] {cap_count} corrective action plans seeded")

print("\n--- Seed Summary -----------------------------")
print(f"  Tenants:  {len(TENANTS)}")
print(f"  Users:    {len(USERS)}")
print(f"  Hazards:  {hazard_count}")
print(f"  Risk Asm: {risk_count}")
print(f"  Reports:  {report_count}")
print(f"  CANs:     {can_count}")
print(f"  CAPs:     {cap_count}")
print("-----------------------------------------------")
print("Done. Run `uvicorn sms_engine.main:app --reload` and check /api/v1/regulator/dashboard")
