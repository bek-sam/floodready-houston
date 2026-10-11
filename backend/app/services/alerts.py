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
