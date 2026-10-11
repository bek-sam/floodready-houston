from datetime import datetime, timedelta, timezone

from app import freshness
from app.db import Report, get_session
from app.services.codes import tag_warnings
from app.services.alerts import get_alerts, is_flood_alert
from app.services.data import haversine_m
from app.services.gauges import nearest_gauges
from app.services.route import load_crossings

RANK = {"ok": 0, "watch": 1, "warning": 2}
CALL = "Call 911 in an emergency."


def crossings_near(lat, lon, radius_m=1000):
    out = []
    for f in load_crossings():
        try:
            x, y = f["geometry"]["coordinates"][:2]
        except Exception:
            continue
        d = haversine_m(lat, lon, y, x)
        if d <= radius_m:
            p = f.get("properties", {})
            out.append((d, p.get("name") or "a flood-prone crossing", p.get("risk")))
    return sorted(out)


def road_reports_near(lat, lon, radius_m=1000, hours=6):
    """Recent community reports of water on roads within radius_m of a point."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    try:
        with get_session() as s:
            rows = s.query(Report).filter(Report.created_at >= cutoff,
                                          Report.kind.in_(("water_over_road", "flooded_road"))).all()
            pts = [(r.lat, r.lon, r.depth_in) for r in rows]
    except Exception:
        return []
    return [p for p in pts if haversine_m(lat, lon, p[0], p[1]) <= radius_m]


async def evaluate(place: dict, simulate: bool = False) -> dict:
    lat, lon = place["lat"], place["lon"]
    reasons, rcodes, level = [], [], "ok"

    def up(l):
        nonlocal level
        if RANK[l] > RANK[level]:
            level = l

    al = await get_alerts(lat, lon)
    flood = [a for a in al["alerts"] if is_flood_alert(a)]
    for a in flood:
        warn = "warning" in (a.get("event") or "").lower()
        up("warning" if warn else "watch")
        reasons.append(f"NWS {a['event']} in effect for this location")
        rcodes.append({"code": "watch.r.nws", "params": {"event": a["event"]}})
    gauges = await nearest_gauges(lat, lon, 3, simulate)
    for g in gauges:
        if g["status"] in ("moderate", "major"):
            up("warning")
        elif g["status"] == "minor":
            up("warning" if simulate else "watch")
        elif g["status"] == "action":
            up("watch")
        else:
            continue
        reasons.append(f"{g['name']} is at {g['status']} stage ({g['stage_ft']} ft)"
                       + (" [simulated]" if simulate else ""))
        rcodes.append({"code": "watch.r.gauge", "params": {"name": g["name"], "status": g["status"], "ft": g["stage_ft"],
                                                          "sim": " [simulated]" if simulate else ""}})
    near = crossings_near(lat, lon)
    if near:
        high = any(c[2] == "high" for c in near)
        if level != "ok" or simulate:
            up("warning" if high else "watch")
        d, name, _ = near[0]
        reasons.append(f"{len(near)} flood-prone crossing(s) within 1 km, nearest: {name} ({d / 1000:.1f} km)")
        rcodes.append({"code": "watch.r.cross", "params": {"n": len(near), "name": name, "km": f"{d / 1000:.1f}"}})
    if not simulate:
        rep = road_reports_near(lat, lon)
        if rep and (len(rep) >= 2 or any((d or 0) >= 6 for _, _, d in rep)):
            up("watch")
            reasons.append(f"{len(rep)} community reports of water on roads nearby (last 6h)")
            rcodes.append({"code": "watch.r.reports", "params": {"n": len(rep)}})
    if simulate:
        up("warning")
        if not reasons:
            reasons.append("Simulated storm conditions")
            rcodes.append({"code": "watch.r.sim", "params": {}})
    mcode = "watch." + level
    if level == "warning":
        msg = f"Flood warning for {place['label']}: avoid low roads and underpasses, move valuables up, and be ready to leave. {CALL}"
    elif level == "watch":
        msg = f"Flood watch for {place['label']}: conditions are building. Check routes before you drive. {CALL}"
    else:
        msg = f"No flood alerts or high gauges near {place['label']} right now. Not official guidance; check weather.gov."
    out = {"id": place["id"], "label": place["label"], "level": level, "reasons": reasons, "alerts": flood,
           "gauges": gauges, "crossings_nearby": len(near), "message": msg,
           "message_code": mcode, "message_params": {"label": place["label"]}, "reason_codes": rcodes}
    if al.get("warnings"):
        out["warnings"] = al["warnings"]
        tag_warnings(out)
    storm = bool(flood) or any(g["status"] in ("action", "minor", "moderate", "major") for g in gauges)
    out["meta"] = freshness.meta("NWS alerts + NOAA NWPS gauges", "live", storm=storm or freshness.storm_on())
    return out
