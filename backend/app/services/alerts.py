from app import freshness
from app.services.codes import tag_warnings
from app.services.http import get_json


async def get_alerts(lat: float, lon: float) -> dict:
    d = await get_json("https://api.weather.gov/alerts/active", {"point": f"{lat:.4f},{lon:.4f}"}, ttl=120)
    if d is None:
        return tag_warnings({"alerts": [], "warnings": ["NWS alerts unavailable right now; check weather.gov"],
                             "meta": freshness.meta("https://api.weather.gov/alerts/active", "cached", as_of=None)})
    alerts = []
    for f in d.get("features", []):
        p = f.get("properties", {})
        alerts.append({"event": p.get("event"), "severity": p.get("severity"), "headline": p.get("headline"),
                       "description": (p.get("description") or "")[:600], "expires": p.get("expires")})
    storm = any(is_flood_alert(a) for a in alerts)
    if storm:
        freshness.mark_storm()
    return {"alerts": alerts, "meta": freshness.meta("https://api.weather.gov/alerts/active", "live", storm=storm or freshness.storm_on())}


FLOOD_WORDS = ("flood", "flash flood", "hurricane", "tropical", "storm surge", "coastal")


def is_flood_alert(a: dict) -> bool:
    return any(w in (a.get("event") or "").lower() for w in FLOOD_WORDS)


AREA_URL = "https://api.weather.gov/alerts/active"
AREA_EVENTS = ("flood warning", "flash flood warning", "flood watch", "flash flood watch", "flood advisory",
               "coastal flood")


def _coords(g):
    if isinstance(g, list):
        if g and isinstance(g[0], (int, float)):
            yield g
        else:
            for x in g:
                yield from _coords(x)


def _intersects(geom: dict, bbox: tuple) -> bool:
    minx, miny, maxx, maxy = bbox
    pts = list(_coords((geom or {}).get("coordinates")))
    if not pts:
        return False
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return not (max(xs) < minx or min(xs) > maxx or max(ys) < miny or min(ys) > maxy)


def parse_bbox(bbox: str):
    try:
        v = tuple(float(x) for x in bbox.split(","))
        return v if len(v) == 4 and v[0] < v[2] and v[1] < v[3] else None
    except Exception:
        return None


def build_area(d: dict, bbox: tuple) -> dict:
    feats, zone_only = [], []
    for f in (d or {}).get("features", []):
        p = f.get("properties") or {}
        ev = (p.get("event") or "")
        if not any(ev.lower().startswith(e) for e in AREA_EVENTS):
            continue
        geom = f.get("geometry")
        if geom:
            if not _intersects(geom, bbox):
                continue
            aid = p.get("id") or f.get("id") or ""
            feats.append({"type": "Feature", "geometry": geom, "properties": {
                "id": aid, "event": ev, "severity": p.get("severity"), "headline": p.get("headline"),
                "expires": p.get("expires"), "has_geometry": True, "area_desc": p.get("areaDesc"),
                "source": f"https://api.weather.gov/alerts/{aid}"}})
        else:
            zone_only.append({"event": ev, "headline": p.get("headline"), "area_desc": p.get("areaDesc"),
                              "expires": p.get("expires")})
    return {"type": "FeatureCollection", "features": feats, "zone_only": zone_only[:50]}


async def area_alerts(bbox: str) -> dict:
    bb = parse_bbox(bbox) or (-96.5, 29.0, -94.5, 30.5)
    d = await get_json(AREA_URL, {"area": "TX"}, ttl=300)
    if not isinstance(d, dict):
        return {"type": "FeatureCollection", "features": [], "zone_only": [],
                "warnings": ["NWS alerts unavailable right now; check weather.gov"],
                "meta": freshness.meta(AREA_URL, "cached", as_of=None)}
    out = build_area(d, bb)
    storm = any(is_flood_alert({"event": f["properties"]["event"]}) and "warning" in f["properties"]["event"].lower()
                for f in out["features"])
    if storm:
        freshness.mark_storm()
    out["meta"] = freshness.meta(AREA_URL, "live", storm=storm or freshness.storm_on())
    return out


def add_simulated_alert(out: dict, lat: float, lon: float) -> dict:
    """Demo only: prepend one clearly labelled fake Flash Flood Warning to a real /alerts response."""
    from datetime import datetime, timedelta, timezone
    area = f"your area ({lat:.3f}, {lon:.3f})"
    sim = {"event": "Flash Flood Warning", "severity": "Severe",
           "headline": f"SIMULATED \u2014 demo only: Flash Flood Warning for {area}",
           "description": "Simulated storm for demonstration. Not a real NWS alert.",
           "expires": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(timespec="seconds"),
           "simulated": True}
    out = dict(out)
    out["alerts"] = [sim] + list(out.get("alerts") or [])
    out["simulated"] = True
    out["meta"] = {**(out.get("meta") or freshness.meta("simulated", "live")), "storm_mode": True}
    return out


def _in_ring(x, y, ring) -> bool:
    inside, n, j = False, len(ring), len(ring) - 1
    for i in range(n):
        xi, yi, xj, yj = ring[i][0], ring[i][1], ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def point_in_geom(x: float, y: float, geom: dict) -> bool:
    """Point-in-Polygon/MultiPolygon (lon, lat); holes respected."""
    t, c = (geom or {}).get("type"), (geom or {}).get("coordinates")
    polys = [c] if t == "Polygon" else c if t == "MultiPolygon" else []
    for rings in polys or []:
        if rings and _in_ring(x, y, rings[0]) and not any(_in_ring(x, y, h) for h in rings[1:]):
            return True
    return False


async def route_warnings(coords: list) -> list[dict]:
    """Active NWS Flood / Flash Flood / Coastal Flood WARNING polygons that the route line passes through."""
    if not coords:
        return []
    xs, ys = [c[0] for c in coords], [c[1] for c in coords]
    bb = (min(xs) - 0.01, min(ys) - 0.01, max(xs) + 0.01, max(ys) + 0.01)
    d = await get_json(AREA_URL, {"area": "TX"}, ttl=300)
    if not isinstance(d, dict):
        return []
    area = build_area(d, bb)
    out = []
    step = max(1, len(coords) // 400)
    pts = coords[::step] + [coords[-1]]
    for f in area["features"]:
        p = f["properties"]
        if "flood" not in p["event"].lower() or "warning" not in p["event"].lower():
            continue
        if any(point_in_geom(x, y, f["geometry"]) for x, y in pts):
            out.append({"event": p["event"], "headline": p.get("headline"), "expires": p.get("expires"), "id": p.get("id")})
    if out:
        freshness.mark_storm()
    return out
