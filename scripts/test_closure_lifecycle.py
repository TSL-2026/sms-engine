"""
Test complete hazard lifecycle: open -> processing (via CAN) -> closed (via verify) -> reopened -> closed
"""
import urllib.request, json

base = "http://127.0.0.1:8000"
reg_headers = {"X-API-Key": "caan-reg-key-2026", "Content-Type": "application/json"}

def api(method, path, headers=None, body=None):
    url = f"{base}{path}"
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"ERROR": e.code, "detail": json.loads(e.read())}

# 1. Pick a Yeti Airlines hazard
print("=== 1. List Yeti Airlines hazards ===")
hazards = api("GET", "/api/v1/operator/yeti-airlines/hazards", {"X-API-Key": "yeti-airlines-key-2026"})
if isinstance(hazards, list) and hazards:
    hazard = hazards[0]
    hid = hazard["id"]
    print(f"  Using: {hazard['hazard_id']} - {hazard['title'][:55]}")
    print(f"  Initial status: {hazard['status']}")

    # 2. Issue a CAN
    print("\n=== 2. Issue CAN ===")
    can_body = {"description": "CAN for lifecycle test", "department_assigned": "Test",
                "priority": "High", "due_date": "2026-07-07"}
    result = api("POST", f"/api/v1/operator/yeti-airlines/hazards/{hid}/can",
                 {"X-API-Key": "yeti-airlines-key-2026"}, can_body)
    print(f"  {result}")

    # 3. Check hazard status (should be 'processing')
    print("\n=== 3. Verify hazard status ===")
    h = api("GET", f"/api/v1/operator/yeti-airlines/hazards/{hid}",
            {"X-API-Key": "yeti-airlines-key-2026"})
    print(f"  Hazard status after CAN: {h.get('hazard',{}).get('status')}")

    # 4. Find the CAN and submit CAP
    print("\n=== 4. Submit CAP ===")
    cans = api("GET", f"/api/v1/operator/yeti-airlines/cans",
               {"X-API-Key": "yeti-airlines-key-2026"})
    if isinstance(cans, list):
        can = [c for c in cans if c.get("hazard_id") == hid][0]
        can_id = can["id"]
        cap_body = {"description": "Lifecycle test CAP", "action_items": [
            {"action": "Test action", "owner": "Test", "target_date": "2026-07-07",
             "status": "pending", "notes": ""}
        ]}
        result = api("POST", f"/api/v1/operator/yeti-airlines/cans/{can_id}/cap",
                     {"X-API-Key": "yeti-airlines-key-2026"}, cap_body)
        print(f"  {result}")

    # 5. Verify CAP as accepted
    print("\n=== 5. Verify CAP (accepted) ===")
    result = api("POST", f"/api/v1/operator/yeti-airlines/caps/{can_id}/verify",
                 {"X-API-Key": "yeti-airlines-key-2026"},
                 {"verdict": "accepted", "notes": "Effectiveness verified - hazard closed"})
    print(f"  {result}")

    # 6. Check hazard is closed
    print("\n=== 6. Hazard should be CLOSED ===")
    h = api("GET", f"/api/v1/operator/yeti-airlines/hazards/{hid}",
            {"X-API-Key": "yeti-airlines-key-2026"})
    print(f"  Status: {h.get('hazard',{}).get('status')}")
    print(f"  Closed at: {h.get('hazard',{}).get('closed_at')}")
    print(f"  Closed by: {h.get('hazard',{}).get('closed_by')}")

    # 7. Test reopen via verify (ineffective)
    print("\n=== 7. Test reopen on another hazard ===")
    h2 = hazards[1]
    hid2 = h2["id"]
    api("POST", f"/api/v1/operator/yeti-airlines/hazards/{hid2}/can",
        {"X-API-Key": "yeti-airlines-key-2026"}, can_body)
    cans2 = api("GET", f"/api/v1/operator/yeti-airlines/cans",
                {"X-API-Key": "yeti-airlines-key-2026"})
    can2 = [c for c in cans2 if c.get("hazard_id") == hid2][0]
    can_id2 = can2["id"]
    api("POST", f"/api/v1/operator/yeti-airlines/cans/{can_id2}/cap",
        {"X-API-Key": "yeti-airlines-key-2026"}, cap_body)
    result = api("POST", f"/api/v1/operator/yeti-airlines/caps/{can_id2}/verify",
                 {"X-API-Key": "yeti-airlines-key-2026"},
                 {"verdict": "ineffective", "notes": "CAP did not resolve issue"})
    print(f"  {result}")
    h2_result = api("GET", f"/api/v1/operator/yeti-airlines/hazards/{hid2}",
                    {"X-API-Key": "yeti-airlines-key-2026"})
    print(f"  Hazard status: {h2_result.get('hazard',{}).get('status')}")

    # 8. Test closure endpoint with lessons learned
    print("\n=== 8. Re-issue CAN for reopened hazard, then use /close endpoint ===")
    re_hid = hid2
    api("POST", f"/api/v1/operator/yeti-airlines/hazards/{re_hid}/can",
        {"X-API-Key": "yeti-airlines-key-2026"}, can_body)
    re_cans = api("GET", f"/api/v1/operator/yeti-airlines/cans",
                  {"X-API-Key": "yeti-airlines-key-2026"})
    re_can = [c for c in re_cans if c.get("hazard_id") == re_hid][0]
    api("POST", f"/api/v1/operator/yeti-airlines/cans/{re_can['id']}/cap",
        {"X-API-Key": "yeti-airlines-key-2026"}, cap_body)
    api("POST", f"/api/v1/operator/yeti-airlines/caps/{re_can['id']}/verify",
        {"X-API-Key": "yeti-airlines-key-2026"},
        {"verdict": "accepted", "notes": "Second attempt successful"})
    result = api("POST", f"/api/v1/operator/yeti-airlines/hazards/{re_hid}/close",
                 {"X-API-Key": "yeti-airlines-key-2026"},
                 {"lessons_learned": "Need more thorough root cause analysis before implementing CAP"})
    print(f"  {result}")
    final = api("GET", f"/api/v1/operator/yeti-airlines/hazards/{re_hid}",
                {"X-API-Key": "yeti-airlines-key-2026"})
    print(f"  Final status: {final.get('hazard',{}).get('status')}")
    print(f"  Lessons learned: {final.get('hazard',{}).get('lessons_learned')}")

print("\n=== Lifecycle test complete ===")
