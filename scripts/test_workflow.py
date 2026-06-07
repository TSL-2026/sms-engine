"""
Test CAN/CAP workflow and CAAN aggregated views via API.
"""
import urllib.request, json

base = "http://127.0.0.1:8000"

def api(method, path, headers=None, body=None):
    url = f"{base}{path}"
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"ERROR": e.code, "detail": json.loads(e.read())}

# 1. List CANs for Buddha Air
print("=== 1. Buddha Air CANs ===")
result = api("GET", "/api/v1/operator/buddha-air/cans", {"X-API-Key": "buddha-air-key-2026"})
print(f"  Total: {len(result)} CANs" if isinstance(result, list) else f"  {result}")
if isinstance(result, list):
    for c in result[:5]:
        print(f"    {c['can_id']} [{c['priority']}] {c['status']} -> {c.get('department_assigned','')}")

# 2. List CANs for Yeti Airlines
print("\n=== 2. Yeti Airlines CANs ===")
result = api("GET", "/api/v1/operator/yeti-airlines/cans", {"X-API-Key": "yeti-airlines-key-2026"})
print(f"  Total: {len(result)} CANs" if isinstance(result, list) else f"  {result}")
if isinstance(result, list):
    for c in result[:5]:
        print(f"    {c['can_id']} [{c['priority']}] {c['status']}")

# 3. Issue a new CAN via API
print("\n=== 3. Issue CAN via API ===")
hazard_id = "hazards_20260607080939979865"  # Buddha Air - Bird strikes
can_body = {
    "description": "Test CAN from API - Bird strike mitigation",
    "department_assigned": "Ground Operations",
    "priority": "High",
    "due_date": "2026-07-07T00:00:00"
}
result = api("POST", f"/api/v1/operator/buddha-air/hazards/{hazard_id}/can",
             {"X-API-Key": "buddha-air-key-2026"}, can_body)
print(f"  {result}")

# 4. Get CAN details
print("\n=== 4. CAN details ===")
cans_list = api("GET", "/api/v1/operator/buddha-air/cans", {"X-API-Key": "buddha-air-key-2026"})
if isinstance(cans_list, list) and cans_list:
    can = cans_list[0]
    can_id = can["id"]
    print(f"  CAN ID: {can['can_id']}, Status: {can['status']}, Hazard: {can['hazard_id']}")

    # 5. Submit CAP
    print("\n=== 5. Submit CAP ===")
    cap_body = {
        "description": "Action plan for bird strike mitigation at Bharatpur",
        "action_items": [
            {"action": "Install bird deterrent system", "owner": "Ground Ops",
             "target_date": "2026-07-15", "status": "pending", "notes": ""}
        ],
        "resource_requirements": "Bird repellent equipment"
    }
    result = api("POST", f"/api/v1/operator/buddha-air/cans/{can_id}/cap",
                 {"X-API-Key": "buddha-air-key-2026"}, cap_body)
    print(f"  {result}")

    # 6. Get CAP
    print("\n=== 6. Get CAP ===")
    result = api("GET", f"/api/v1/operator/buddha-air/cans/{can_id}/cap",
                 {"X-API-Key": "buddha-air-key-2026"})
    if isinstance(result, dict) and "can_id" in result:
        print(f"  CAP status: {result['status']}, items: {len(result.get('action_items',[]))}")
    else:
        print(f"  {result}")

# 7. CAAN aggregated view
print("\n=== 7. CAAN Aggregated View ===")
result = api("GET", "/api/v1/regulator/hazards/aggregated", {"X-API-Key": "caan-reg-key-2026"})
s = result.get("summary", {})
print(f"  Total hazards: {s.get('total_hazards')}")
print(f"  Total open: {s.get('total_open_hazards')}")
print(f"  Risk distribution: {s.get('risk_distribution')}")
print(f"  Top categories: {s.get('top_categories')}")
print(f"  Operators: {len(result.get('by_operator',[]))}")
print(f"  Leading indicator type: {type(result.get('leading_indicators')).__name__}")

# 8. List CANs for Summit Air
print("\n=== 8. Summit Air CANs with CAPs ===")
result = api("GET", "/api/v1/operator/summit-air/cans", {"X-API-Key": "summit-air-key-2026"})
if isinstance(result, list):
    for c in result:
        cap = api("GET", f"/api/v1/operator/summit-air/cans/{c['id']}/cap",
                  {"X-API-Key": "summit-air-key-2026"})
        cap_status = cap.get("status", "N/A") if isinstance(cap, dict) else "N/A"
        print(f"  {c['can_id']} [{c['priority']}] {c['status']} -> CAP: {cap_status}")
