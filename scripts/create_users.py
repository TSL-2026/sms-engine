import urllib.request, json

users = [
    {"tenant_id": "buddha-air", "email": "safety@buddhaair.com", "name": "Buddha Safety Manager", "role": "safety_manager"},
    {"tenant_id": "yeti-airlines", "email": "safety@yetiairlines.com", "name": "Yeti Safety Manager", "role": "safety_manager"},
    {"tenant_id": "shree-airlines", "email": "safety@shreeairlines.com", "name": "Shree Safety Manager", "role": "safety_manager"},
    {"tenant_id": "nepal-airlines", "email": "safety@nepalairlines.com", "name": "NAC Safety Manager", "role": "safety_manager"},
    {"tenant_id": "saurya-airlines", "email": "safety@sauryaairlines.com", "name": "Saurya Safety Manager", "role": "safety_manager"},
    {"tenant_id": "summit-air", "email": "safety@summitair.com", "name": "Summit Safety Manager", "role": "safety_manager"},
]

headers = {
    "X-API-Key": "caan-reg-key-2026",
    "Content-Type": "application/json",
}

for u in users:
    tid = u.pop("tenant_id")
    url = f"http://127.0.0.1:8000/api/v1/admin/tenants/{tid}/users"
    data = json.dumps(u).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req)
        print(f"OK  {tid:20s} -> {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"ERR {tid:20s} -> {e.code} {e.read().decode()}")
