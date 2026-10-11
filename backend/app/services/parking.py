"""Park-my-car check: assess a parking spot with existing services. Records-based, never a safety claim."""
import asyncio
import math

from app import freshness
from app.services.alerts import get_alerts, is_flood_alert
from app.services.data import haversine_m
from app.services.http import get_json
from app.services.risk import EPQS, get_risk
from app.services.watch import crossings_near

CROSSING_M = 300
RING_M = 400
MIN_GAIN_FT = 3.0
LIMITS = ("Based on flood records and maps, not a prediction for this storm. "
          "It cannot tell you a spot is safe. Call 911 in an emergency.")
SOURCE = "FEMA NFHL + Harvey extent + USGS EPQS + NWS alerts + city crossing list"


def _offset(lat, lon, bearing_deg, m):
    dlat = m * math.cos(math.radians(bearing_deg)) / 111320
    dlon = m * math.sin(math.radians(bearing_deg)) / (111320 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


async def _elev_at(lat, lon):
    d = await get_json(EPQS, {"x": lon, "y": lat, "units": "Feet", "wkid": 4326}, ttl=3600)
    try:
        v = float(d["value"])
        return v if v > -1000 else None
    except Exception:
        return None


async def higher_ground(lat, lon, elev):
    """Sample 8 points ~400 m away; return the highest one that is MIN_GAIN_FT above the spot, else None."""
    if elev is None:
        return None
    pts = [_offset(lat, lon, b, RING_M) for b in range(0, 360, 45)]
    els = await asyncio.gather(*[_elev_at(*p) for p in pts])
    best = None
    for (la, lo), e in zip(pts, els):
        if e is not None and e - elev >= MIN_GAIN_FT and (best is None or e > best["elevation_ft"]):
            best = {"lat": round(la, 5), "lon": round(lo, 5), "elevation_ft": round(e, 1), "gain_ft": round(e - elev, 1),
                    "distance_m": RING_M,
                    "maps_url": f"https://www.google.com/maps/dir/?api=1&destination={la:.5f},{lo:.5f}&travelmode=driving"}
    return best


def verdict_for(reasons: list[dict], flood_alert: bool) -> dict:
    if reasons or flood_alert:
        return {"level": "move", "headline_code": "p30.park.move.h", "detail_code": "p30.park.move.d",
                "headline": "Consider moving your car to higher ground before heavy rain",
                "detail": "Flood records or an active alert flag this spot. Higher ground is not a guarantee of safety."}
    return {"level": "no_flags", "headline_code": "p30.park.ok.h", "detail_code": "p30.park.ok.d",
            "headline": "No flood flags found for this spot in our records",
            "detail": "That does not mean the spot is safe. Check the forecast and local alerts."}


async def assess(lat: float, lon: float, address: str | None = None) -> dict:
    risk, alerts = await asyncio.gather(get_risk(lat, lon), get_alerts(lat, lon))
    reasons = []
    zone = risk.get("fema_zone")
    if risk.get("sfha") or (zone or "").upper().startswith(("A", "V")):
        reasons.append({"code": "fema_zone", "params": {"zone": zone}, "text": f"FEMA mapped flood zone {zone}"})
    hv = risk.get("harvey") or {}
    if hv.get("flooded") is True:
        reasons.append({"code": "harvey", "params": {}, "text": "This spot is inside the mapped Hurricane Harvey flood extent"})
    cross = [{"name": n, "distance_m": round(d), "risk": r} for d, n, r in crossings_near(lat, lon, CROSSING_M)]
    if cross:
        reasons.append({"code": "crossing", "params": {"n": len(cross), "m": CROSSING_M}, "text": f"{len(cross)} known flood-prone crossing(s) within {CROSSING_M} m"})
    if risk.get("low_ground"):
        reasons.append({"code": "low_ground", "params": {}, "text": "Lower than nearby gauges' reference ground (approximate)"})
    flood_alerts = [a for a in alerts.get("alerts", []) if is_flood_alert(a)]
    elev = risk.get("elevation_ft")
    hg = await higher_ground(lat, lon, elev) if (reasons or flood_alerts) else None
    v = verdict_for(reasons, bool(flood_alerts))
    out = {"lat": lat, "lon": lon, "address": address, "verdict": v["level"], "headline": v["headline"], "detail": v["detail"],
           "headline_code": v["headline_code"], "detail_code": v["detail_code"], "limits_code": "p30.park.limits",
           "reasons": reasons,
           "fema_zone": zone, "harvey_flooded": hv.get("flooded"), "elevation_ft": elev,
           "crossings_within_300m": cross,
           "active_flood_alerts": [{"event": a.get("event"), "headline": a.get("headline"), "expires": a.get("expires")} for a in flood_alerts],
           "higher_ground": hg, "limits": LIMITS,
           "sources": ["https://msc.fema.gov/portal/home", "https://api.weather.gov", "https://epqs.nationalmap.gov"]}
    w = list(risk.get("warnings", [])) + list(alerts.get("warnings", []))
    if w:
        out["warnings"] = w
    return freshness.with_meta(out, source=SOURCE, freshness="live", storm=bool(flood_alerts) or freshness.storm_on())
