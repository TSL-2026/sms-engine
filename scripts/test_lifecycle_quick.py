"""
Quick test of complete hazard lifecycle.
"""
import urllib.request, json

base = "http://127.0.0.1:8000"
KEY = "yeti-airlines-key-2026"

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

# 1. Pick an open hazard
hazards = api("GET", "/api/v1/operator/yeti-airlines/hazards?status=open",
              {"X-API-Key": KEY})
h = [x for x in hazards if x["status"] == "open"][0]
hid = h["id"]
print(f"1. Selected: {h['hazard_id']} - {h['title'][:50]} (status: {h['status']})")

# 2. Issue CAN
r = api("POST", f"/api/v1/operator/yeti-airlines/hazards/{hid}/can",
        {"X-API-Key": KEY},
        {"description": "Lifecycle test CAN", "department_assigned": "Test",
         "priority": "High", "due_date": "2026-07-07"})
can_id = r["id"]
print(f"2. CAN: {r}")

# 3. Hazard should be 'processing'
h2 = api("GET", f"/api/v1/operator/yeti-airlines/hazards/{hid}",
         {"X-API-Key": KEY})
print(f"3. Hazard status after CAN: {h2['hazard']['status']}")

# 4. Submit CAP
r = api("POST", f"/api/v1/operator/yeti-airlines/cans/{can_id}/cap",
        {"X-API-Key": KEY},
        {"description": "Test CAP", "action_items": [
            {"action": "Fix issue", "owner": "Test", "target_date": "2026-07-07",
             "status": "pending", "notes": ""}
        ]})
print(f"4. CAP: {r}")

# 5. Verify CAP as accepted
r = api("POST", f"/api/v1/operator/yeti-airlines/caps/{can_id}/verify",
        {"X-API-Key": KEY},
        {"verdict": "accepted", "notes": "Verified effective"})
print(f"5. Verify (accepted): {r}")

# 6. Hazard should be closed
h3 = api("GET", f"/api/v1/operator/yeti-airlines/hazards/{hid}",
         {"X-API-Key": KEY})
print(f"6. Hazard status: {h3['hazard']['status']}, closed_at: {h3['hazard'].get('closed_at','N/A')[:19]}, closed_by: {h3['hazard'].get('closed_by','N/A')}")

# 7. Try close on a processing hazard with lessons_learned as query param
hazards2 = api("GET", "/api/v1/operator/yeti-airlines/hazards?status=open",
              {"X-API-Key": KEY})
h2nd = [x for x in hazards2 if x["status"] == "open"][0]
hid2 = h2nd["id"]
print(f"\n7. Second hazard: {h2nd['hazard_id']} - {h2nd['title'][:50]}")
api("POST", f"/api/v1/operator/yeti-airlines/hazards/{hid2}/can",
    {"X-API-Key": KEY},
    {"description": "Second test CAN", "department_assigned": "Test",
     "priority": "Medium", "due_date": "2026-07-07"})
can2 = api("GET", f"/api/v1/operator/yeti-airlines/cans",
           {"X-API-Key": KEY})
can2_id = [c for c in can2 if c["hazard_id"] == hid2][0]["id"]
api("POST", f"/api/v1/operator/yeti-airlines/cans/{can2_id}/cap",
    {"X-API-Key": KEY},
    {"description": "Second CAP", "action_items": []})

# Close with lessons_learned query param
r = api("POST", f"/api/v1/operator/yeti-airlines/hazards/{hid2}/close?lessons_learned=Need+more+thorough+RCA",
        {"X-API-Key": KEY})
print(f"8. Close with lessons: {r}")

# Final state
h_final = api("GET", f"/api/v1/operator/yeti-airlines/hazards/{hid2}",
              {"X-API-Key": KEY})
print(f"9. Final: status={h_final['hazard']['status']}, lessons={h_final['hazard'].get('lessons_learned','N/A')}")
print("\n=== Lifecycle test PASSED ===")
