import urllib.request, json

tenants = [
    {"id": "buddha-air", "name": "Buddha Air", "code": "BHA", "fleet": "ATR 72/42", "base": "Kathmandu"},
    {"id": "yeti-airlines", "name": "Yeti Airlines", "code": "NYT", "fleet": "ATR 72/42", "base": "Kathmandu"},
    {"id": "shree-airlines", "name": "Shree Airlines", "code": "SHA", "fleet": "CRJ-200, Dash 8, Mi-17", "base": "Kathmandu"},
    {"id": "nepal-airlines", "name": "Nepal Airlines Corporation", "code": "NAC", "fleet": "A320, A330, ATR 42, Twin Otter", "base": "Kathmandu"},
    {"id": "saurya-airlines", "name": "Saurya Airlines", "code": "SAU", "fleet": "CRJ-200", "base": "Kathmandu"},
    {"id": "summit-air", "name": "Summit Air", "code": "SMA", "fleet": "L-410, Dornier 228", "base": "Kathmandu"},
]

url = "http://127.0.0.1:8000/api/v1/admin/tenants"
headers = {
    "X-API-Key": "caan-reg-key-2026",
    "Content-Type": "application/json",
}

for t in tenants:
    data = json.dumps(t).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req)
        print(f"OK  {t['name']:35s} -> {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"ERR {t['name']:35s} -> {e.code} {e.read().decode()}")
