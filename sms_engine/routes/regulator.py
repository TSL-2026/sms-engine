from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from sms_engine.database import tenants, reports, hazards, risk_assessments, cans
from sms_engine.auth import CurrentUser, get_current_user, verify_regulator_key

router = APIRouter(prefix="/api/v1/regulator")

STATUS_ORDER = {"open": 0, "under_mitigation": 1, "accepted": 2, "closed": 3}


@router.get("/dashboard")
def regulator_dashboard(user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    all_tenants = tenants.list()
    result = []
    for t in all_tenants:
        tid = t["id"]
        tenant_hazards = _all_hazards(tid)
        result.append({
            "tenant": t,
            "report_count": len(reports.list({"tenant_id": tid})),
            "open_hazard_count": len([h for h in tenant_hazards if h.get("status") == "open"]),
            "open_can_count": len([c for c in _all_cans() if c.get("tenant_id") == tid and c.get("status") != "Accepted"]),
        })
    return {"tenants": result}


@router.get("/operators")
def list_operators(user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    return tenants.list()


@router.get("/hazards/aggregated")
async def get_aggregated_hazards(
    api_key: str = Depends(verify_regulator_key),
):
    now = datetime.now(timezone.utc)
    tenant_ids = [
        "buddha-air", "yeti-airlines", "shree-airlines",
        "nepal-airlines", "saurya-airlines", "summit-air",
    ]

    aggregated = []
    total_by_risk = {"intolerable": 0, "tolerable": 0, "acceptable": 0}
    hazards_by_category = {}
    total_open_hazards = 0

    for tid in tenant_ids:
        hazards_list = await get_hazards_by_tenant(tid)

        intolerable = len([h for h in hazards_list if h.get("risk_zone") == "intolerable"])
        tolerable = len([h for h in hazards_list if h.get("risk_zone") == "tolerable"])
        acceptable = len([h for h in hazards_list if h.get("risk_zone") == "acceptable"])
        open_hazards = len([h for h in hazards_list if h.get("status") == "Open"])

        total_by_risk["intolerable"] += intolerable
        total_by_risk["tolerable"] += tolerable
        total_by_risk["acceptable"] += acceptable
        total_open_hazards += open_hazards

        for h in hazards_list:
            cat = h.get("category", "Uncategorized")
            hazards_by_category[cat] = hazards_by_category.get(cat, 0) + 1

        aggregated.append({
            "operator_id": tid,
            "operator_name": get_tenant_name(tid),
            "total_hazards": len(hazards_list),
            "intolerable": intolerable,
            "tolerable": tolerable,
            "acceptable": acceptable,
            "open_hazards": open_hazards,
        })

    leading_indicators = await calculate_leading_indicators(tenant_ids)

    aggregated.sort(key=lambda x: (x["intolerable"], x["total_hazards"]), reverse=True)

    return {
        "summary": {
            "total_operators": len(tenant_ids),
            "total_hazards": sum(o["total_hazards"] for o in aggregated),
            "total_open_hazards": total_open_hazards,
            "risk_distribution": total_by_risk,
            "top_categories": sorted(hazards_by_category.items(), key=lambda x: x[1], reverse=True)[:5],
        },
        "by_operator": aggregated,
        "leading_indicators": leading_indicators,
        "generated_at": now.isoformat(),
    }


@router.get("/hazards/leading-indicators")
def leading_indicators(user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    all_hazards = _all_hazards()
    assessments = _all_assessments()

    hazard_by_tenant = defaultdict(list)
    for h in all_hazards:
        hazard_by_tenant[h.get("tenant_id", "unknown")].append(h)

    category_trends = Counter()
    tenant_categories = defaultdict(Counter)
    zone_trends = {"intolerable": 0, "tolerable": 0, "acceptable": 0}
    recent_hazards = []
    now = datetime.now(timezone.utc)

    for h in all_hazards:
        cat = h.get("category", "unknown")
        category_trends[cat] += 1
        tid = h.get("tenant_id", "unknown")
        tenant_categories[tid][cat] += 1
        risk = _get_latest_risk(h)
        if risk:
            zone_trends[risk] += 1
        created = h.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created)
                if (now - dt).days < 90:
                    recent_hazards.append(h)
            except ValueError:
                pass

    recent_category = Counter(h.get("category", "unknown") for h in recent_hazards)
    rising_risk = _detect_rising_risk(all_hazards)
    recurring = _detect_recurring_patterns(all_hazards)

    return {
        "total_hazards": len(all_hazards),
        "zone_distribution": zone_trends,
        "category_distribution_all": dict(category_trends),
        "category_distribution_last_90_days": dict(recent_category),
        "rising_risk_indicators": rising_risk,
        "recurring_patterns": recurring,
        "per_operator_category_breakdown": {tid: dict(c) for tid, c in tenant_categories.items()},
        "note": "Leading indicators highlight patterns that predict future incidents — increasing frequency, rising severity, or recurring themes.",
    }


@router.get("/hazards/lagging-indicators")
def lagging_indicators(user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    all_hazards = _all_hazards()
    all_reports_list = _all_reports()
    all_cans_list = _all_cans()
    assessments = _all_assessments()

    mor_reports = [r for r in all_reports_list if r.get("report_type") == "MOR"]
    vsr_reports = [r for r in all_reports_list if r.get("report_type") == "VSR"]
    escalation_rate = len([r for r in all_reports_list if r.get("hazard_id")]) / max(len(all_reports_list), 1)

    closed_hazards = [h for h in all_hazards if h.get("status") == "closed"]
    resolution_times = []
    for h in closed_hazards:
        created = h.get("created_at", "")
        closed = h.get("closed_at", "")
        if created and closed:
            try:
                delta = datetime.fromisoformat(closed) - datetime.fromisoformat(created)
                resolution_times.append(delta.days)
            except (ValueError, TypeError):
                pass
    avg_resolution = round(sum(resolution_times) / max(len(resolution_times), 1), 1) if resolution_times else 0

    can_completion = len([c for c in all_cans_list if c.get("status") == "Accepted"])
    can_overdue = len([c for c in all_cans_list if c.get("status") not in ("Accepted",)])

    by_operator = defaultdict(lambda: {"hazards": 0, "mor": 0, "vsr": 0, "cans": 0, "closed": 0})
    for h in all_hazards:
        tid = h.get("tenant_id", "unknown")
        by_operator[tid]["hazards"] += 1
        if h.get("status") == "closed":
            by_operator[tid]["closed"] += 1
    for r in all_reports_list:
        tid = r.get("tenant_id", "unknown")
        by_operator[tid]["mor" if r.get("report_type") == "MOR" else "vsr"] += 1
    for c in all_cans_list:
        tid = c.get("tenant_id", "unknown")
        by_operator[tid]["cans"] += 1

    return {
        "total_mor": len(mor_reports),
        "total_vsr": len(vsr_reports),
        "mor_to_hazard_escalation_rate": round(escalation_rate * 100, 1),
        "average_resolution_time_days": avg_resolution,
        "can_completion_rate": f"{can_completion}/{len(all_cans_list)}" if all_cans_list else "0/0",
        "can_overdue_count": can_overdue,
        "per_operator_summary": dict(by_operator),
        "note": "Lagging indicators measure past safety performance — incident rates, resolution times, and escalation patterns.",
    }


@router.get("/safety-performance/dashboard")
def safety_performance_dashboard(user: CurrentUser = Depends(get_current_user)):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    all_tenants = tenants.list()
    all_hazards = _all_hazards()
    all_assessments_list = _all_assessments()
    all_cans_list = _all_cans()
    all_reports_list = _all_reports()

    rows = []
    for t in all_tenants:
        tid = t["id"]
        tenant_hazards = [h for h in all_hazards if h.get("tenant_id") == tid]
        tenant_assessments = [a for a in all_assessments_list if a.get("hazard_id") in {h["id"] for h in tenant_hazards}]
        zone_counts = Counter(a.get("risk_zone", "") for a in tenant_assessments)
        category_counts = Counter(h.get("category", "") for h in tenant_hazards)
        top_cat = category_counts.most_common(1)[0][0] if category_counts else ""

        closed_hazards = [h for h in tenant_hazards if h.get("status") == "closed"]
        resolution_days = []
        for h in closed_hazards:
            created = h.get("created_at", "")
            closed = h.get("closed_at", "")
            if created and closed:
                try:
                    delta = datetime.fromisoformat(closed) - datetime.fromisoformat(created)
                    resolution_days.append(delta.days)
                except (ValueError, TypeError):
                    pass
        avg_res = round(sum(resolution_days) / max(len(resolution_days), 1), 1) if resolution_days else None

        rows.append({
            "tenant": {"id": tid, "name": t.get("name", tid), "code": t.get("code", "")},
            "total_hazards": len(tenant_hazards),
            "intolerable": zone_counts.get("intolerable", 0),
            "tolerable": zone_counts.get("tolerable", 0),
            "acceptable": zone_counts.get("acceptable", 0),
            "top_risk_category": top_cat,
            "avg_resolution_days": avg_res,
            "open_hazards": len([h for h in tenant_hazards if h.get("status") == "open"]),
            "can_count": len([c for c in all_cans_list if c.get("tenant_id") == tid]),
        })

    # Cross-operator aggregates
    total_intolerable = sum(r["intolerable"] for r in rows)
    total_tolerable = sum(r["tolerable"] for r in rows)
    total_hazards = sum(r["total_hazards"] for r in rows)

    return {
        "operators": rows,
        "aggregates": {
            "total_operators": len([t for t in all_tenants if t.get("id") != "caan"]),
            "total_hazards_across_operators": total_hazards,
            "total_intolerable": total_intolerable,
            "total_tolerable": total_tolerable,
            "total_acceptable": sum(r["acceptable"] for r in rows),
            "overall_high_risk_pct": round(total_intolerable / max(total_hazards, 1) * 100, 1),
        },
        "leading_alerts": _compute_leading_alerts(all_hazards, all_cans_list),
    }


@router.get("/operators/compare")
def compare_operators(
    metrics: str = Query("risk,category", description="Comma-separated: risk,category,resolution"),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.is_regulator:
        raise HTTPException(403, "Regulator access required")
    metric_list = [m.strip() for m in metrics.split(",")]
    all_tenants = [t for t in tenants.list() if t.get("id") != "caan"]
    all_hazards = _all_hazards()
    all_assessments_list = _all_assessments()

    result = []
    for t in all_tenants:
        tid = t["id"]
        tenant_hazards = [h for h in all_hazards if h.get("tenant_id") == tid]
        entry = {"tenant": {"id": tid, "name": t.get("name", tid), "code": t.get("code", "")}}
        for m in metric_list:
            if m == "risk":
                assessments = [a for a in all_assessments_list if a.get("hazard_id") in {h["id"] for h in tenant_hazards}]
                zone_counts = Counter(a.get("risk_zone", "") for a in assessments)
                entry["intolerable"] = zone_counts.get("intolerable", 0)
                entry["tolerable"] = zone_counts.get("tolerable", 0)
                entry["acceptable"] = zone_counts.get("acceptable", 0)
            if m == "category":
                cat_counts = Counter(h.get("category", "") for h in tenant_hazards)
                entry["top_category"] = cat_counts.most_common(1)[0][0] if cat_counts else ""
                entry["categories"] = dict(cat_counts)
            if m == "resolution":
                closed = [h for h in tenant_hazards if h.get("status") == "closed"]
                days = []
                for h in closed:
                    c, cl = h.get("created_at", ""), h.get("closed_at", "")
                    if c and cl:
                        try:
                            days.append((datetime.fromisoformat(cl) - datetime.fromisoformat(c)).days)
                        except (ValueError, TypeError):
                            pass
                entry["avg_resolution_days"] = round(sum(days) / max(len(days), 1), 1) if days else None
                entry["closed_count"] = len(closed)
        result.append(entry)

    return {"comparison": result, "metrics_requested": metric_list}


def _compute_leading_alerts(all_hazards: list, all_cans: list) -> list:
    alerts = []
    now = datetime.now(timezone.utc)
    hazard_by_tenant = defaultdict(list)
    for h in all_hazards:
        hazard_by_tenant[h.get("tenant_id", "unknown")].append(h)

    for tid, hlist in hazard_by_tenant.items():
        recent = [h for h in hlist if _days_since(h.get("created_at", ""), now) is not None and _days_since(h.get("created_at", ""), now) < 90]
        zone_counts = Counter()
        for h in hlist:
            risk = _get_latest_risk(h)
            if risk:
                zone_counts[risk] += 1
        recent_zone = Counter()
        for h in recent:
            risk = _get_latest_risk(h)
            if risk:
                recent_zone[risk] += 1
        if zone_counts.get("intolerable", 0) >= 2:
            alerts.append({
                "tenant_id": tid,
                "type": "HIGH_INTOLERABLE_COUNT",
                "severity": "CRITICAL",
                "message": f"{tid} has {zone_counts['intolerable']} intolerable hazards — requires immediate regulatory attention.",
            })
        if len(hlist) >= 4 and len(recent) >= len(hlist) * 0.5:
            alerts.append({
                "tenant_id": tid,
                "type": "HIGH_RECENT_ACTIVITY",
                "severity": "WARNING",
                "message": f"{tid} has {len(recent)} of {len(hlist)} hazards reported in last 90 days — safety surge detected.",
            })
    return alerts


def _days_since(iso_str: str, now: datetime) -> int | None:
    if not iso_str:
        return None
    try:
        return (now - datetime.fromisoformat(iso_str)).days
    except (ValueError, TypeError):
        return None


def _get_latest_risk(hazard: dict) -> str | None:
    assessments = _all_assessments()
    matching = [a for a in assessments if a.get("hazard_id") == hazard.get("id")]
    if not matching:
        return None
    return sorted(matching, key=lambda a: a.get("assessed_at", ""), reverse=True)[0].get("risk_zone")


def _detect_rising_risk(all_hazards: list) -> list:
    now = datetime.now(timezone.utc)
    by_category = defaultdict(list)
    for h in all_hazards:
        cat = h.get("category", "unknown")
        by_category[cat].append(h)
    indicators = []
    for cat, hlist in by_category.items():
        recent = [h for h in hlist if _days_since(h.get("created_at", ""), now) is not None and _days_since(h.get("created_at", ""), now) < 90]
        older = [h for h in hlist if _days_since(h.get("created_at", ""), now) is not None and _days_since(h.get("created_at", ""), now) >= 90]
        if len(recent) > len(older) and len(hlist) >= 3:
            indicators.append({
                "category": cat,
                "total": len(hlist),
                "recent_90d": len(recent),
                "older": len(older),
                "trend": "RISING",
                "note": f"'{cat}' hazards increasing — {len(recent)} reported in last 90 days vs {len(older)} previously.",
            })
    return indicators


def _detect_recurring_patterns(all_hazards: list) -> list:
    title_groups = defaultdict(list)
    for h in all_hazards:
        key = h.get("title", "")[:30]
        title_groups[key].append(h)
    patterns = []
    for key, group in title_groups.items():
        if len(group) >= 2:
            tenants_involved = list(set(h.get("tenant_id", "?") for h in group))
            patterns.append({
                "pattern_key": key + "...",
                "occurrences": len(group),
                "tenants_involved": tenants_involved,
                "hazard_ids": [h.get("hazard_id", h.get("id", "?")) for h in group],
            })
    patterns.sort(key=lambda p: p["occurrences"], reverse=True)
    return patterns[:10]


async def calculate_leading_indicators(tenant_ids: list) -> dict:
    indicators = {
        "trending_hazard_categories": [],
        "operators_with_increasing_hazards": [],
        "operators_with_high_open_hazards": [],
        "risk_trend": "stable",
        "alert_recommendations": [],
    }

    for tid in tenant_ids:
        hazards_list = await get_hazards_by_tenant(tid)

        open_count = len([h for h in hazards_list if h.get("status") == "open"])
        if open_count >= 3:
            indicators["operators_with_high_open_hazards"].append({
                "operator": tid,
                "open_hazards": open_count,
            })

        categories = {}
        for h in hazards_list:
            cat = h.get("category", "Uncategorized")
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in categories.items():
            if count >= 2:
                indicators["trending_hazard_categories"].append({
                    "operator": tid,
                    "category": cat,
                    "count": count,
                })

    if indicators["operators_with_high_open_hazards"]:
        operators = [o["operator"] for o in indicators["operators_with_high_open_hazards"]]
        indicators["alert_recommendations"].append(
            f"High number of open hazards: {', '.join(operators)}. Recommend follow-up on corrective actions."
        )
        indicators["risk_trend"] = "increasing"

    if indicators["trending_hazard_categories"]:
        categories = list(set(t["category"] for t in indicators["trending_hazard_categories"]))
        indicators["alert_recommendations"].append(
            f"Recurring hazards detected in categories: {', '.join(categories)}. Consider industry-wide safety promotion."
        )

    if not indicators["alert_recommendations"]:
        indicators["alert_recommendations"].append("No immediate leading indicator alerts. Safety trends are stable.")
        indicators["risk_trend"] = "stable"

    return indicators


async def get_hazards_by_tenant(tenant_id: str) -> list:
    from sms_engine.database import hazards as hdb
    hazards_list = hdb.list({"tenant_id": tenant_id})
    for h in hazards_list:
        risk = _get_latest_risk(h)
        if risk:
            h["risk_zone"] = risk
    return hazards_list


def get_tenant_name(tenant_id: str) -> str:
    names = {
        "buddha-air": "Buddha Air",
        "yeti-airlines": "Yeti Airlines",
        "shree-airlines": "Shree Airlines",
        "nepal-airlines": "Nepal Airlines Corporation",
        "saurya-airlines": "Saurya Airlines",
        "summit-air": "Summit Air",
        "sita-air": "Sita Air",
        "caan": "Civil Aviation Authority of Nepal",
    }
    return names.get(tenant_id, tenant_id.replace("-", " ").title())


def _all_hazards(tenant_id: str | None = None):
    from sms_engine.database import hazards as hdb
    if tenant_id:
        return hdb.list({"tenant_id": tenant_id})
    return hdb.list()


def _all_assessments():
    from sms_engine.database import risk_assessments as rdb
    return rdb.list()


def _all_cans():
    from sms_engine.database import cans as cdb
    return cdb.list()


def _all_reports():
    from sms_engine.database import reports as rdb
    return rdb.list()
