"""
Seed CAN/CAP records for all 6 Nepal operators.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timezone, timedelta
from sms_engine.database import hazards as hazards_db, cans as cans_db, caps as caps_db

# Hazard keywords to match, with CAN details
can_plans = {
    "buddha-air": [
        ("bird", "Medium", "Ground Operations", 30, "submitted"),
        ("baggage", "Medium", "Ground Operations", 45, None),
        ("fatigue", "Medium", "Flight Operations", 45, "under_review"),
    ],
    "yeti-airlines": [
        ("Lukla", "High", "Ground Operations", 14, "approved"),
        ("Mountain weather", "Medium", "Flight Operations", 60, None),
        ("ground handling", "Low", "Ground Operations", 90, "draft"),
    ],
    "shree-airlines": [
        ("Cargo", "High", "Cargo Operations", 21, "submitted"),
        ("brake cooling", "Medium", "Maintenance", 45, None),
        ("Mi-17", "High", "Maintenance", 21, "under_review"),
        ("helipad", "High", "Infrastructure", 90, None),
    ],
    "nepal-airlines": [
        ("Aging", "Medium", "CAMO", 60, "approved"),
        ("wildlife", "Medium", "Ground Operations", 30, "submitted"),
        ("outstation", "Medium", "CAMO", 60, None),
    ],
    "saurya-airlines": [
        ("hot/high", "Medium", "Flight Operations", 45, "implemented"),
        ("dispatch", "High", "Flight Operations", 30, "under_review"),
        ("slot", "Low", "Operations", 60, None),
    ],
    "summit-air": [
        ("STOL performance", "High", "Flight Operations", 30, "approved"),
        ("weather", "Medium", "Flight Operations", 45, "submitted"),
        ("cargo", "High", "Ground Operations", 21, None),
    ],
}

now = datetime.now(timezone.utc)
year = now.strftime("%Y")
total_cans = 0

for tenant_id, plans in can_plans.items():
    tenant_hazards = hazards_db.list({"tenant_id": tenant_id})
    existing = cans_db.list({"tenant_id": tenant_id})
    can_count = len(existing)
    tenant_can_ids = {c.get("hazard_id") for c in existing}
    print(f"\n--- {tenant_id} ---")

    for kw, priority, dept, days_due, cap_status in plans:
        matching = [h for h in tenant_hazards if kw.lower() in h.get("title", "").lower()]
        if not matching:
            print(f"  [SKIP] No hazard matching '{kw}'")
            continue
        hazard = matching[0]
        if hazard["id"] in tenant_can_ids:
            print(f"  [SKIP] {hazard['title'][:50]} (CAN already exists)")
            continue

        can_count += 1
        total_cans += 1
        can_id_str = f"CAN-{year}-{can_count:04d}"
        due = now + timedelta(days=days_due)

        can_doc = {
            "can_id": can_id_str,
            "tenant_id": tenant_id,
            "hazard_id": hazard["id"],
            "issued_by": f"{tenant_id}-safety",
            "issued_date": now.isoformat(),
            "due_date": due.isoformat(),
            "priority": priority,
            "description": f"Corrective action for: {hazard['title']}",
            "department_assigned": dept,
            "status": "Issued",
        }
        doc_id = cans_db.add(can_doc)
        hazards_db.update(hazard["id"], {"status": "under_mitigation"})
        print(f"  {can_id_str} -> {hazard['title'][:55]} ({priority})")

        if cap_status and cap_status != "none":
            items = [
                {"action": "Investigate root cause", "owner": dept,
                 "target_date": due.isoformat(),
                 "status": "completed" if cap_status == "implemented" else "in_progress",
                 "completed_date": now.isoformat() if cap_status == "implemented" else "",
                 "notes": ""},
                {"action": "Implement corrective measures", "owner": dept,
                 "target_date": due.isoformat(),
                 "status": "completed" if cap_status in ("approved", "implemented") else "in_progress",
                 "completed_date": now.isoformat() if cap_status == "implemented" else "",
                 "notes": ""},
                {"action": "Verify effectiveness", "owner": dept,
                 "target_date": (due + timedelta(days=30)).isoformat(),
                 "status": "pending",
                 "completed_date": "", "notes": ""},
            ]
            cap_doc = {
                "can_id": doc_id,
                "submitted_by": f"{tenant_id}-safety",
                "status": cap_status,
                "description": f"Plan to address: {hazard['title']}",
                "action_items": items,
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

print(f"\n=== Total CANs created: {total_cans} ===")
