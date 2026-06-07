import urllib.request, json

tenant_keys = {
    "buddha-air": "buddha-air-key-2026",
    "yeti-airlines": "yeti-airlines-key-2026",
    "shree-airlines": "shree-airlines-key-2026",
    "nepal-airlines": "nepal-airlines-key-2026",
    "saurya-airlines": "saurya-airlines-key-2026",
    "summit-air": "summit-air-key-2026",
}

hazards_by_tenant = {
    "buddha-air": [
        {"title": "ATR 72 flap asymmetry on approach", "description": "Recurring flap asymmetry warnings during approach into Kathmandu RWY 02", "category": "technical"},
        {"title": "Bird strike near Simara", "description": "Multiple bird strike encounters during descent below 5000 ft", "category": "operational"},
        {"title": "Crew fatigue on double-day roster", "description": "Pilot reports of fatigue due to early morning and late evening pairing", "category": "human_factors"},
    ],
    "yeti-airlines": [
        {"title": "Runway excursion risk at Lukla", "description": "Slippery runway surface during monsoon at VNLK", "category": "operational"},
        {"title": "ATR 42 pressurization fault", "description": "Cabin altitude warning during climb to FL250", "category": "technical"},
        {"title": "Inadequate baggage loading documentation", "description": "Weight and balance sheets missing for 3 flights in one week", "category": "organizational"},
    ],
    "shree-airlines": [
        {"title": "CRJ-200 engine surge on start", "description": "Engine compressor stall during startup at Kathmandu", "category": "technical"},
        {"title": "Dash 8 tail strike on landing", "description": "Tail contact during flare at Pokhara", "category": "operational"},
        {"title": "Mi-17 brownout landing", "description": "Loss of visual reference during landing at high-altitude helipad", "category": "environmental"},
    ],
    "nepal-airlines": [
        {"title": "A320 TCAS RA near Delhi FIR boundary", "description": "Resolution advisory during handover due to opposite traffic", "category": "operational"},
        {"title": "Twin Otter crosswind landing limit exceeded", "description": "Crosswind component above fleet limit at Jomsom", "category": "operational"},
        {"title": "Maintenance record discrepancy", "description": "Component logbook entries missing for A330 APU", "category": "organizational"},
    ],
    "saurya-airlines": [
        {"title": "CRJ-200 hydraulic leak left system", "description": "Hydraulic fluid loss on left system during pushback", "category": "technical"},
        {"title": "Near miss with drone at Biratnagar", "description": "Unmanned aircraft sighted within 200 ft on final approach", "category": "environmental"},
        {"title": "Unstabilized approach rate", "description": "Multiple unstabilized approaches in last quarter exceeding 5% threshold", "category": "human_factors"},
    ],
    "summit-air": [
        {"title": "L-410 icing encounter", "description": "Structural icing during descent into Simikot", "category": "environmental"},
        {"title": "Dornier 228 navigation failure", "description": "GNSS signal loss in mountainous terrain west of Kathmandu", "category": "technical"},
        {"title": "Fuel contamination report", "description": "Water contamination found in fuel sample during pre-flight", "category": "operational"},
    ],
}

for tenant_id, hazards in hazards_by_tenant.items():
    api_key = tenant_keys[tenant_id]
    url = f"http://127.0.0.1:8000/api/v1/operator/{tenant_id}/hazards"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }
    print(f"\n--- {tenant_id} ---")
    for h in hazards:
        data = json.dumps(h).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            resp = urllib.request.urlopen(req)
            print(f"  OK  {h['title'][:50]:50s} -> {resp.read().decode()}")
        except urllib.error.HTTPError as e:
            print(f"  ERR {h['title'][:50]:50s} -> {e.code} {e.read().decode()}")
