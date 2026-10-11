"""Galveston tide anomaly (NOAA CO-OPS) + NHC active Atlantic storms. Cached 8 min."""
import asyncio
import json
from datetime import datetime, timedelta, timezone

from app.services.data import haversine_m
from app.services.http import get_json

STATION = "8771450"
STATION_NAME = "Galveston Pier 21"
API = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
NHC = "https://www.nhc.noaa.gov/CurrentStorms.json"
TTL = 480
STALE_MIN = 30


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _p(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _tide(obs, pred) -> dict:
    t = {"station": f"{STATION_NAME} ({STATION})", "observed_ft": None, "predicted_ft": None,
         "anomaly_ft": None, "as_of": None, "stale": None, "datum": "MLLW", "note": "Unavailable",
         "note_code": "coastal.unavail", "params": {}}
    rows = (obs or {}).get("data") or []
    if not rows:
        return t
    last = rows[-1]
    o = _num(last.get("v"))
    when = last.get("t")
    t["as_of"] = when
    if o is None:
        return t
    t["observed_ft"] = o
    preds = {p.get("t"): _num(p.get("v")) for p in (pred or {}).get("predictions") or []}
    # nearest hourly prediction to the observation time
    lt = _p(when)
    best = None
    if lt:
        for k, v in preds.items():
            pt = _p(k)
            if pt is not None and v is not None and (best is None or abs(pt - lt) < best[0]):
                best = (abs(pt - lt), v)
    if best and best[0] <= timedelta(minutes=35):
        t["predicted_ft"] = best[1]
        t["anomaly_ft"] = round(o - best[1], 2)
        a = t["anomaly_ft"]
        t["note"] = f"Galveston tide: {abs(a):.1f} ft {'above' if a >= 0 else 'below'} forecast"
        t["note_code"], t["params"] = ("coastal.above" if a >= 0 else "coastal.below"), {"ft": f"{abs(a):.1f}"}
    else:
        t["note"] = "Observed level available; matching prediction unavailable"
        t["note_code"] = "coastal.nopred"
    return t


GALV = (29.31, -94.79)


def _storms(d) -> list[dict]:
    """Only storms relevant to the Texas/Gulf coast: Gulf/W-Caribbean box, or advisory text naming Texas."""
    out = []
    for s in (d or {}).get("activeStorms") or []:
        if not str(s.get("id", "")).lower().startswith("al"):
            continue  # Atlantic basin only
        lat, lon = _num(s.get("latitudeNumeric")), _num(s.get("longitudeNumeric"))
        in_box = lat is not None and lon is not None and 18 <= lat <= 31 and -98 <= lon <= -80
        txt = json.dumps({k: v for k, v in s.items() if k not in ("id", "binNumber")}).lower()
        texas = "texas" in txt and any(w in txt for w in ("watch", "warning"))
        if not (in_box or texas):
            continue
        dist = round(haversine_m(GALV[0], GALV[1], lat, lon) / 1609.344) if lat is not None and lon is not None else None
        out.append({"name": s.get("name"), "type": s.get("classification"), "lat": lat, "lon": lon,
                    "gulf_of_mexico": in_box, "relevant": True, "distance_to_galveston_mi": dist,
                    "advisory_url": (s.get("publicAdvisory") or {}).get("url") or "https://www.nhc.noaa.gov/"})
    return out


async def coastal() -> dict:
    now = datetime.now(timezone.utc)
    base = {"product": "water_level", "station": STATION, "datum": "MLLW", "time_zone": "gmt",
            "units": "english", "format": "json", "application": "floodready", "date": "latest"}
    pred = {"product": "predictions", "station": STATION, "datum": "MLLW", "time_zone": "gmt", "units": "english",
            "format": "json", "application": "floodready", "interval": "h",
            "begin_date": (now - timedelta(hours=3)).strftime("%Y%m%d %H:%M"),
            "end_date": (now + timedelta(hours=1)).strftime("%Y%m%d %H:%M")}
    obs, pr, nhc = await asyncio.gather(get_json(API, base, ttl=TTL), get_json(API, pred, ttl=TTL),
                                        get_json(NHC, ttl=TTL))
    # date=latest returns the single newest reading; make the observation window comparable
    t = _tide(obs, pr)
    ts = _p(t["as_of"])
    if ts:
        t["stale"] = (now - ts) > timedelta(minutes=STALE_MIN)
    return {"tide": t, "active_storms": _storms(nhc), "nhc_available": nhc is not None}
