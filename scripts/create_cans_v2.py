"""
Create sample CAN/CAP records - uses actual hazard titles from the DB.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timezone, timedelta
from sms_engine.database import hazards as hazards_db, cans as cans_db, caps as caps_db

# Print actual hazard titles so we can match properly
for tid in ["buddha-air","yeti-airlines","shree-airlines","nepal-airlines","saurya-airlines","summit-air"]:
    hlist = hazards_db.list({"tenant_id": tid})
    print(f"\n{tid}:")
    for h in hlist:
        print(f"  [{h['id']}] {h['title'][:70]}")

# Now match by keywords instead of exact title
can_plans = {
    "buddha-air": [
        {"kw": "brake", "priority": "High", "dept": "Maintenance", "days_due": 30},
        {"kw": "fatigue", "priority": "Medium", "dept": "Flight Operations", "days_due": 45},
    ],
    "yeti-airlines": [
        {"kw": "Lukla", "priority": "High", "dept": "Ground Operations", "days_due": 14},
        {"kw": "Mountain wave", "priority": "Medium", "dept": "Flight Operations", "days_due": 60},
    ],
    "shree-airlines": [
        {"kw": "Cargo", "priority": "High", "dept": "Cargo Operations", "days_due": 21},
        {"kw": "helipad", "priority": "High", "dept": "Infrastructure", "days_due": 90},
    ],
    "nepal-airlines": [
        {"kw": "Aging", "priority": "Medium", "dept": "CAMO", "days_due": 60},
        {"kw": "Fuel quality", "priority": "High", "dept": "Ground Operations", "days_due": 30},
    ],
    "saurya-airlines": [
        {"kw": "hot/high", "priority": "Medium", "dept": "Flight Operations", "days_due": 45},
    ],
    "summit-air": [
        {"kw": "STOL performance", "priority": "High", "dept": "Flight Operations", "days_due": 30},
        {"kw": "remote strip", "priority": "Medium", "dept": "Infrastructure", "days_due": 60},
    ],
}

now = datetime.now(timezone.utc)
year = now.strftime("%Y")

for tenant_id, plans in can_plans.items():
    tenant_hazards = hazards_db.list({"tenant_id": tenant_id})
    existing_cans = cans_db.list({"tenant_id": tenant_id})
    can_count = len(existing_cans)
    print(f"\n--- {tenant_id} ---")

    for plan in plans:
        matching = [h for h in tenant_hazards if plan["kw"].lower() in h.get("title", "").lower()]
        if not matching:
            print(f"  No hazard matching '{plan['kw']}'")
            continue
        hazard = matching[0]
        can_count += 1
        can_id_str = f"CAN-{year}-{can_count:04d}"
        due = now + timedelta(days=plan["days_due"])
        doc = {
            "can_id": can_id_str,
            "tenant_id": tenant_id,
            "hazard_id": hazard["id"],
            "issued_by": f"{tenant_id}-safety",
            "issued_date": now.isoformat(),
            "due_date": due.isoformat(),
            "priority": plan["priority"],
            "description": f"Corrective action for: {hazard['title']}",
            "department_assigned": plan["dept"],
            "status": "Issued",
        }
        doc_id = cans_db.add(doc)
        hazards_db.update(hazard["id"], {"status": "under_mitigation"})
        print(f"  {can_id_str} -> {hazard['title'][:55]} ({plan['priority']})")

        # Create CAP for first CAN of each tenant (alternating statuses)
        cap_statuses = ["submitted", "under_review", "approved", "implemented"]
        cap_status = cap_statuses[can_count % len(cap_statuses)]
        description = f"Plan to address: {hazard['title']}"
        action_items = [
            {"action": f"Investigate root cause", "owner": plan["dept"],
             "target_date": due.isoformat(),
             "status": "completed" if cap_status == "implemented" else "in_progress",
             "completed_date": now.isoformat() if cap_status == "implemented" else "",
             "notes": ""},
            {"action": "Implement corrective measures", "owner": plan["dept"],
             "target_date": due.isoformat(),
             "status": "completed" if cap_status in ("approved", "implemented") else "in_progress",
             "completed_date": now.isoformat() if cap_status == "implemented" else "",
             "notes": ""},
        ]
        cap_doc = {
            "can_id": doc_id,
            "submitted_by": f"{tenant_id}-safety",
            "status": cap_status,
            "description": description,
            "action_items": action_items,
            "resource_requirements": "Engineering time, spare parts as needed",
            "reviewed_by": "caan-regulator" if cap_status in ("under_review", "approved", "implemented") else "",
            "review_notes": "CAP under review" if cap_status == "under_review" else "Approved" if cap_status == "approved" else "Implemented and verified" if cap_status == "implemented" else "",
            "rejection_reason": "",
            "approved_by": "caan-regulator" if cap_status in ("approved", "implemented") else "",
            "approved_at": (now - timedelta(days=7)).isoformat() if cap_status in ("approved", "implemented") else "",
            "completed_date": now.isoformat() if cap_status == "implemented" else "",
        }
        caps_db.add(cap_doc)
        print(f"    + CAP ({cap_status})")
