"""
Replace old dummy hazards with corrected realistic Nepal aviation scenarios.
Uses the database module directly to clean + re-seed hazards.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timezone
from sms_engine.database import hazards as hazards_db

tenant_ids = ["buddha-air", "yeti-airlines", "shree-airlines",
              "nepal-airlines", "saurya-airlines", "summit-air"]

# Delete all existing hazards for these tenants
for tid in tenant_ids:
    existing = hazards_db.list({"tenant_id": tid})
    for h in existing:
        hazards_db.delete(h["id"])
    print(f"Deleted {len(existing)} existing hazards for {tid}")

# New hazard definitions per tenant
hazards_by_tenant = {
    "buddha-air": [
        {"title": "ATR brake wear from frequent short-haul sectors",
         "description": "Excessive brake wear observed on ATR 72/42 fleets operating 5-6 daily short sectors between Kathmandu, Pokhara, Bharatpur, and Nepalgunj. Brake temperatures exceed limits before turnaround.",
         "category": "technical"},
        {"title": "Passenger baggage weight discrepancies at Pokhara",
         "description": "Reported discrepancies between declared and actual checked baggage weights at Pokhara airport, leading to potential C of G errors on ATR departures.",
         "category": "operational"},
        {"title": "Rapid weather changes on Pokhara-Jomsom route",
         "description": "Sudden visibility loss and wind direction shifts on the Pokhara-Jomsom sector, creating hazardous approach conditions for ATR aircraft.",
         "category": "environmental"},
        {"title": "Crew fatigue from 5-6 sector days",
         "description": "Crew rostered for 5-6 sectors daily with inadequate rest between pairings, leading to self-reported fatigue and degraded performance on approach.",
         "category": "human_factors"},
        {"title": "Bird strikes during monsoon at Bharatpur",
         "description": "Increased bird activity around Bharatpur runway during monsoon season resulting in multiple bird strike encounters on approach and departure.",
         "category": "environmental"},
    ],
    "yeti-airlines": [
        {"title": "Lukla runway condition monitoring",
         "description": "Lukla (VNLK) STOL runway slope gradient and surface friction degradation during monsoon. Critical for ATR STOL operations with limited go-around margin.",
         "category": "operational"},
        {"title": "Mountain wave turbulence on Kathmandu-Lukla route",
         "description": "Severe mountain wave turbulence encounters en route to Lukla, causing altitude deviations and passenger injuries in moderate to severe turbulence.",
         "category": "environmental"},
        {"title": "Remote station ground handling equipment",
         "description": "Inadequate ground power units (GPU) and towbars at remote STOL stations like Simikot, Taplejung, leading to engineering delays and battery depletions.",
         "category": "ground_operations"},
        {"title": "Weight and balance for STOL operations",
         "description": "Inconsistent weight and balance calculations for ATR STOL operations from high-altitude runways, increasing risk of performance exceedance on departure.",
         "category": "procedural"},
    ],
    "shree-airlines": [
        {"title": "CRJ-200 brake cooling time between sectors",
         "description": "Insufficient brake cooling time between CRJ-200 shuttle sectors, resulting in overheated brakes and increased risk of brake fire or rejected takeoff.",
         "category": "technical"},
        {"title": "Helicopter-pilot terrain familiarity in mountain operations",
         "description": "Mi-17 pilots unfamiliar with high-altitude helipad terrain profiles in western Nepal, increasing risk of controlled flight into terrain (CFIT).",
         "category": "training"},
        {"title": "Cargo load securing on Dash 8 combi flights",
         "description": "Improper cargo restraint on Dash 8 combi-configuration flights causing shift of load during turbulence, affecting C of G and flight handling.",
         "category": "cargo_operations"},
        {"title": "Remote helipad surface conditions",
         "description": "Poorly maintained high-altitude helipad surfaces with loose stones, FOD, and inadequate markings creating dynamic rollover and FOD ingestion risks.",
         "category": "infrastructure"},
        {"title": "Multi-fleet type maintenance complexity",
         "description": "CRJ-200, Dash 8, and Mi-17 fleet diversity creates certification, tooling, and training challenges for engineering team, increasing error risk.",
         "category": "organizational"},
    ],
    "nepal-airlines": [
        {"title": "Aging aircraft maintenance documentation",
         "description": "A320/A330 airframe aging programs generating excessive outstanding Airworthiness Directives and Service Bulletins with incomplete compliance records.",
         "category": "technical"},
        {"title": "International/domestic crew transition procedures",
         "description": "Pilot transitions between international (A320/A330) and domestic (ATR 42, Twin Otter) operations with differing procedures, language, and ATC environments.",
         "category": "operational"},
        {"title": "Twin Otter STOL remote station logistics",
         "description": "Spare parts and tooling availability for Twin Otter fleet at remote STOL airstrips, causing extended AOG situations in locations like Jomsom and Simikot.",
         "category": "operational"},
        {"title": "Fuel quality verification at small airports",
         "description": "Fuel filtration and quality testing equipment unavailable or poorly maintained at remote airports, creating risk of contaminated fuel being used.",
         "category": "infrastructure"},
        {"title": "Oversight of outstation maintenance",
         "description": "Line maintenance oversight gap at outstations where limited engineer coverage leads to deferred defect logging and repeat discrepancies.",
         "category": "organizational"},
    ],
    "saurya-airlines": [
        {"title": "CRJ-200 hot/high performance calculations",
         "description": "Performance margins for CRJ-200 departures from hot and high airports exceeding weight limits, requiring incorrect assumption of reserves.",
         "category": "technical"},
        {"title": "Single fleet dispatch reliability",
         "description": "Complete reliance on single CRJ-200 fleet for scheduled ops with zero backup, leading to pressure to dispatch with minor defects to maintain schedule.",
         "category": "technical"},
        {"title": "Kathmandu slot coordination",
         "description": "Slot coordination issues at Kathmandu causing extended ground holds in congested periods, pushing duty times and inducing operational pressure.",
         "category": "operational"},
    ],
    "summit-air": [
        {"title": "L-410 STOL performance at high altitude",
         "description": "L-410 takeoff and climb performance degradation at high-altitude STOL strips above 9,000 ft, requiring precise weight calculations with minimal margins.",
         "category": "technical"},
        {"title": "Dornier 228 remote strip condition assessment",
         "description": "Unpaved airstrip surface deterioration at remote locations, creating risk of tyre burst, propeller strike, or directional control loss on landing.",
         "category": "infrastructure"},
        {"title": "Cargo loading procedures at Lukla",
         "description": "Incorrect cargo distribution on Dornier 228 at Lukla, with urgent loading under time pressure leading to C of G outside certified envelope.",
         "category": "ground_operations"},
        {"title": "Weather minima compliance pressure",
         "description": "Operational pressure to commence or continue approaches below company weather minima at remote STOL fields to avoid diversions and schedule delays.",
         "category": "operational"},
    ],
}

year = datetime.now(timezone.utc).strftime("%Y")

for tenant_id, hazards in hazards_by_tenant.items():
    count = len(hazards_db.list({"tenant_id": tenant_id}))
    print(f"\n--- {tenant_id} ({len(hazards)} hazards) ---")
    for h in hazards:
        count += 1
        hazard_id = f"HR-{year}-{count:04d}"
        doc = {
            "tenant_id": tenant_id,
            "hazard_id": hazard_id,
            "title": h["title"],
            "description": h["description"],
            "category": h["category"],
            "source_report_ids": [],
            "status": "open",
            "created_by": f"{tenant_id}-safety",
        }
        doc_id = hazards_db.add(doc)
        print(f"  {hazard_id}  {h['title'][:60]}")
