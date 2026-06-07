"""
Create sample CAN/CAP records for 6 Nepal operators.
Uses the database module directly and the API.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timezone, timedelta
from sms_engine.database import hazards as hazards_db, cans as cans_db, caps as caps_db

# Map operators to their hazards and CAN descriptions
can_data = {
    "buddha-air": [
        {"hazard_title": "ATR brake wear from frequent short-haul sectors", "priority": "High", "dept": "Maintenance", "days_due": 30},
        {"hazard_title": "Crew fatigue from 5-6 sector days", "priority": "Medium", "dept": "Flight Operations", "days_due": 45},
    ],
    "yeti-airlines": [
        {"hazard_title": "Lukla runway condition monitoring", "priority": "High", "dept": "Ground Operations", "days_due": 14},
        {"hazard_title": "Mountain wave turbulence on Kathmandu-Lukla route", "priority": "Medium", "dept": "Flight Operations", "days_due": 60},
    ],
    "shree-airlines": [
        {"hazard_title": "Cargo load securing on Dash 8 combi flights", "priority": "High", "dept": "Cargo Operations", "days_due": 21},
        {"hazard_title": "Remote helipad surface conditions", "priority": "High", "dept": "Infrastructure", "days_due": 90},
    ],
    "nepal-airlines": [
        {"hazard_title": "Aging aircraft maintenance documentation", "priority": "Medium", "dept": "CAMO", "days_due": 60},
        {"hazard_title": "Fuel quality verification at small airports", "priority": "High", "dept": "Ground Operations", "days_due": 30},
    ],
    "saurya-airlines": [
        {"hazard_title": "CRJ-200 hot/high performance calculations", "priority": "Medium", "dept": "Flight Operations", "days_due": 45},
    ],
    "summit-air": [
        {"hazard_title": "L-410 STOL performance at high altitude", "priority": "High", "dept": "Flight Operations", "days_due": 30},
        {"hazard_title": "Dornier 228 remote strip condition assessment", "priority": "Medium", "dept": "Infrastructure", "days_due": 60},
    ],
}

now = datetime.now(timezone.utc)
year = now.strftime("%Y")

for tenant_id, cans in can_data.items():
    tenant_hazards = hazards_db.list({"tenant_id": tenant_id})
    if not tenant_hazards:
        print(f"No hazards found for {tenant_id}")
        continue

    existing_cans = cans_db.list({"tenant_id": tenant_id})
    can_count = len(existing_cans)

    print(f"\n--- {tenant_id} ---")
    for item in cans:
        matching = [h for h in tenant_hazards if item["hazard_title"] in h.get("title", "")]
        if not matching:
            print(f"  Hazard not found: {item['hazard_title']}")
            continue

        hazard = matching[0]
        can_count += 1
        can_id_str = f"CAN-{year}-{can_count:04d}"
        due = now + timedelta(days=item["days_due"])
        doc = {
            "can_id": can_id_str,
            "tenant_id": tenant_id,
            "hazard_id": hazard["id"],
            "issued_by": f"{tenant_id}-safety",
            "issued_date": now.isoformat(),
            "due_date": due.isoformat(),
            "priority": item["priority"],
            "description": f"Corrective action for: {item['hazard_title']}",
            "department_assigned": item["dept"],
            "status": "Issued",
        }
        doc_id = cans_db.add(doc)
        hazards_db.update(hazard["id"], {"status": "under_mitigation"})
        print(f"  {can_id_str} -> {item['hazard_title'][:50]} ({item['priority']})")

        # Create a CAP for the first CAN of each tenant (various statuses)
        if can_count % 2 == 1 or can_count == 1:
            cap_statuses = ["submitted", "under_review", "approved", "implemented"]
            cap_status = cap_statuses[(can_count - 1) % len(cap_statuses)]
            cap_doc = {
                "can_id": doc_id,
                "submitted_by": f"{tenant_id}-safety",
                "status": cap_status,
                "description": f"Plan to address: {item['hazard_title']}",
                "action_items": [
                    {"action": f"Investigate root cause of {item['hazard_title']}", "owner": item["dept"], "target_date": due.isoformat(), "status": "completed" if cap_status == "implemented" else "in_progress"},
                    {"action": "Implement corrective measures", "owner": item["dept"], "target_date": due.isoformat(), "status": "in_progress" if cap_status in ("under_review", "approved", "implemented") else "pending"},
                ],
                "resource_requirements": "Engineering time, spare parts as needed",
                "reviewed_by": "caan-regulator" if cap_status in ("under_review", "approved", "implemented") else "",
                "review_notes": "Under review by CAAN" if cap_status == "under_review" else "Approved" if cap_status == "approved" else "Implemented and verified" if cap_status == "implemented" else "",
            }
            if cap_status == "approved":
                cap_doc["approved_by"] = "caan-regulator"
                cap_doc["approved_at"] = now.isoformat()
            if cap_status == "implemented":
                cap_doc["approved_by"] = "caan-regulator"
                cap_doc["approved_at"] = (now - timedelta(days=7)).isoformat()
                cap_doc["completed_date"] = now.isoformat()
            caps_db.add(cap_doc)
            print(f"    + CAP ({cap_status})")
