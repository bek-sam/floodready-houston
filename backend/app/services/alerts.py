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
