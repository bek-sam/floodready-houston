"""Route safety check: OSRM route + crossings near it + live conditions."""
from app.services import diskcache
from app.services.alerts import get_alerts, is_flood_alert
from app.services.data import haversine_m, load_json
from app.services.gauges import nearest_gauges
from app.services.http import get_json

OSRM = "https://router.project-osrm.org/route/v1/driving/{a},{b};{c},{d}"
BUFFER_M = 75
REPORT_BUFFER_M = 100
HIGH_DEPTH_IN = 6


def recent_reports() -> list[dict]:
    """Community reports from the last 24h (empty list if the DB is unavailable)."""
    from datetime import datetime, timedelta, timezone
    try:
        from app.db import Report, get_session
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        with get_session() as s:
            rows = s.query(Report).order_by(Report.created_at.desc()).limit(500).all()
            out = []
            for r in rows:
                ts = r.created_at
                if ts is None:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    out.append({"lat": r.lat, "lon": r.lon, "kind": r.kind, "depth_in": r.depth_in,
                                "note": r.note, "created_at": ts.isoformat()})
            return out
    except Exception:
        return []


def load_crossings() -> list[dict]:
    d = load_json("crossings.geojson", {}) or {}
    return d.get("features", [])


def _min_dist_m(lat, lon, coords) -> float:
    # coords are [lon, lat]; check vertices plus midpoints (route vertices are dense with overview=full)
    best = 1e12
    prev = None
    for x, y in coords:
        best = min(best, haversine_m(lat, lon, y, x))
        if prev:
            best = min(best, haversine_m(lat, lon, (y + prev[1]) / 2, (x + prev[0]) / 2))
        prev = (x, y)
    return best


async def check_route(origin: dict, destination: dict, simulate: bool = False) -> dict:
    warnings = []
    o, d = origin, destination
    url = OSRM.format(a=o["lon"], b=o["lat"], c=d["lon"], d=d["lat"])
    rkey = f"{o['lat']:.4f},{o['lon']:.4f};{d['lat']:.4f},{d['lon']:.4f}"
    data = diskcache.get("routes", rkey)
    if not data:
        data = await get_json(url, {"overview": "full", "geometries": "geojson"}, ttl=600)
        if data and data.get("routes"):
            diskcache.put("routes", rkey, data)
    fallback = False
    try:
        line = data["routes"][0]["geometry"]
    except Exception:
        fallback = True
        warnings.append("Routing service unavailable; showing a straight line, not a real route")
        line = {"type": "LineString", "coordinates": [[o["lon"], o["lat"]], [d["lon"], d["lat"]]]}
    coords = line["coordinates"]

    hazards, high, deep_report = [], False, None
    for f in load_crossings():
        try:
            lon, lat = f["geometry"]["coordinates"][:2]
        except Exception:
            continue
        if _min_dist_m(lat, lon, coords) <= BUFFER_M:
            p = f.get("properties", {})
            reasons = p.get("reasons") or []
            hazards.append({"crossing_id": p.get("id"), "name": p.get("name"), "lat": lat, "lon": lon,
                            "reason": reasons[0] if reasons else "Known flood-prone crossing"})
            high = high or p.get("risk") == "high"

    # community reports from the last 24h within 100 m of the route
    for rep in recent_reports():
        if _min_dist_m(rep["lat"], rep["lon"], coords) <= REPORT_BUFFER_M:
            depth = rep.get("depth_in")
            hazards.append({"kind": "report", "crossing_id": None, "name": "Community report", "lat": rep["lat"],
                            "lon": rep["lon"], "depth_in": depth, "report_kind": rep.get("kind"),
                            "reported_at": rep.get("created_at"),
                            "reason": "Community report" + (f": about {depth:g} in of water" if depth is not None else "")
                            + (f" ({rep['note']})" if rep.get("note") else "")})
            if depth is not None and depth >= HIGH_DEPTH_IN:
                high = True
                deep_report = depth

    # live conditions near the route midpoint
    mid = coords[len(coords) // 2]
    active, conds = simulate, []
    if simulate:
        conds.append("simulated storm")
    al = await get_alerts(mid[1], mid[0])
    fl = [a for a in al["alerts"] if is_flood_alert(a)]
    if fl:
        active = True
        conds.append(fl[0]["event"])
    if al.get("warnings"):
        warnings += al["warnings"]
    if deep_report is not None:  # a fresh deep-water report is itself evidence of active flooding
        active = True
        conds.append(f"community report of {deep_report:g} in of water")
    if hazards:
        for g in await nearest_gauges(mid[1], mid[0], 3, simulate):
            if g["status"] in ("action", "minor", "moderate", "major"):
                active = True
                conds.append(f"{g['name']} gauge at {g['status']} stage")
                break

    if hazards and high and active:
        verdict = "avoid"
        msg = (f"Avoid this route. It passes {len(hazards)} flood-prone crossing(s) "
               f"({', '.join(h['name'] or 'unnamed' for h in hazards[:3])}) and conditions are active ({'; '.join(conds)}). "
               "Turn around, don't drown. Call 911 if you are in danger.")
    elif hazards:
        verdict = "caution"
        msg = (f"Use caution. This route crosses {len(hazards)} known flood-prone spot(s) "
               f"({', '.join(h['name'] or 'unnamed' for h in hazards[:3])}). No active flood conditions detected right now, "
               "but check alerts before you go in rain.")
    elif fallback:
        verdict = "caution"
        msg = "Route unavailable, check manually. We could not get a real driving route, so no flood check was possible. Never drive through floodwater."
    else:
        verdict = "safe"
        msg = "No known flood-prone crossings on this route — conditions can change fast; never drive into water."
    n_rep = sum(1 for h in hazards if h.get("kind") == "report")
    if n_rep:
        msg += f" {n_rep} community report{'s' if n_rep != 1 else ''} on this route in the last 24 hours."
    out = {"route": line, "hazards": hazards, "verdict": verdict, "message": msg, "report_count": n_rep}
    if warnings:
        out["warnings"] = warnings
    return out


# Pre-seeded demo routes (OSRM results are cached in backend/.cache/routes.json).
DEMO_ROUTES = [
    {"label": "Downtown: Allen Parkway underpass", "origin": {"lat": 29.7648, "lon": -95.3665}, "destination": {"lat": 29.7648, "lon": -95.3560}},
    {"label": "UH campus to Downtown", "origin": {"lat": 29.7199, "lon": -95.3422}, "destination": {"lat": 29.7607, "lon": -95.3695}},
    {"label": "Meyerland to Downtown", "origin": {"lat": 29.6786, "lon": -95.4640}, "destination": {"lat": 29.7607, "lon": -95.3695}},
    {"label": "Meyerland to UH campus", "origin": {"lat": 29.6786, "lon": -95.4640}, "destination": {"lat": 29.7199, "lon": -95.3422}},
]
