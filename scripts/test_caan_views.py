import urllib.request, json

base = "http://127.0.0.1:8000"
headers = {"X-API-Key": "caan-reg-key-2026"}

endpoints = [
    ("GET", "/health"),
    ("GET", "/api/v1/regulator/operators"),
    ("GET", "/api/v1/regulator/hazards/aggregated"),
    ("GET", "/api/v1/regulator/hazards/leading-indicators"),
    ("GET", "/api/v1/regulator/hazards/lagging-indicators"),
    ("GET", "/api/v1/regulator/safety-performance/dashboard"),
    ("GET", "/api/v1/regulator/operators/compare"),
]

for method, path in endpoints:
    url = f"{base}{path}"
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"\n{'='*60}")
        print(f"{method} {path}")
        print(f"{'='*60}")
        print(json.dumps(data, indent=2)[:2000])
    except urllib.error.HTTPError as e:
        print(f"\n{'='*60}")
        print(f"{method} {path} -> ERROR {e.code}")
        print(f"{'='*60}")
        print(e.read().decode()[:500])
