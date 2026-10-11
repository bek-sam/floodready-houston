"""Rain next 24 h at a point: NWS gridpoint QPF (6 h windows, mm -> in) + hourly probability of precipitation."""
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app import freshness
from app.services.http import get_json

NWS = "https://api.weather.gov"
SOURCE = "NWS gridpoint forecast (api.weather.gov)"
SOURCE_URL = "https://www.weather.gov"
TTL = 900  # 15 min; freshness.effective_ttl caps this to 90 s in storm mode (api.weather.gov host)
LOCAL = ZoneInfo("America/Chicago")
NOTE = "Forecast amounts are NWS model estimates, 6-hour totals. Not official guidance; check weather.gov."
WINDOW_IN = 1.0
POP_PCT = 60
_DUR = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?$")


def _parse_valid(vt: str):
    """'2026-10-11T12:00:00+00:00/PT6H' -> (start, end) aware datetimes, or None."""
    try:
        s, d = vt.split("/")
        start = datetime.fromisoformat(s.replace("Z", "+00:00"))
        m = _DUR.match(d)
        days, hrs, mins = (int(x or 0) for x in m.groups())
        return start, start + timedelta(days=days, hours=hrs, minutes=mins)
    except Exception:
        return None


def _local(dt: datetime) -> str:
    return dt.astimezone(LOCAL).strftime("%-I %p %a")


def parse_qpf(grid: dict, now: datetime, hours: int = 24) -> list[dict]:
    vals = (((grid or {}).get("properties") or {}).get("quantitativePrecipitation") or {}).get("values") or []
    uom = (((grid or {}).get("properties") or {}).get("quantitativePrecipitation") or {}).get("uom", "wmoUnit:mm")
    end_h = now + timedelta(hours=hours)
    out = []
    for v in vals:
        w = _parse_valid(v.get("validTime", ""))
        mm = v.get("value")
        if not w or mm is None:
            continue
        s, e = w
        if e <= now or s >= end_h:
            continue
        inches = float(mm) / 25.4 if "mm" in uom else float(mm)
        out.append({"start": s.isoformat(), "end": e.isoformat(), "inches": round(inches, 2), "label": f"{_local(s)}"})
    return sorted(out, key=lambda x: x["start"])


def parse_pop(hourly: dict, now: datetime, hours: int = 24) -> list[dict]:
    out = []
    end_h = now + timedelta(hours=hours)
    for p in ((hourly or {}).get("properties") or {}).get("periods") or []:
        try:
            s = datetime.fromisoformat(p["startTime"])
            e = datetime.fromisoformat(p["endTime"])
        except Exception:
            continue
        if e <= now or s >= end_h:
            continue
        pop = (p.get("probabilityOfPrecipitation") or {}).get("value")
        out.append({"start": s.isoformat(), "pop_pct": None if pop is None else int(pop), "short": p.get("shortForecast")})
    return out[:hours]


def build(qpf: list[dict], pop: list[dict]) -> dict:
    total = round(sum(w["inches"] for w in qpf), 2)
    wet = max(qpf, key=lambda w: w["inches"], default=None)
    wettest = {"start": wet["start"], "end": wet["end"], "inches": wet["inches"]} if wet and wet["inches"] > 0 else None
    pops = [p["pop_pct"] for p in pop if p["pop_pct"] is not None]
    max_pop = max(pops) if pops else None
    action = {"show": False, "text": None, "window_start": None}
    hit = next((w for w in qpf if w["inches"] >= WINDOW_IN), None)
    start = hit["start"] if hit else None
    if not hit and max_pop is not None and max_pop >= POP_PCT:
        p = next(p for p in pop if p["pop_pct"] == max_pop)
        start = p["start"]
    if start:
        when = _local(datetime.fromisoformat(start))
        action = {"show": True, "window_start": start,
                  "text": f"Leave before {when} if you need to cross a flood-prone road. Heavy rain is possible; this is a forecast, not a safety guarantee."}
    return {"windows": qpf, "total_inches": total, "wettest_window": wettest, "pop_hourly": pop,
            "max_pop_pct": max_pop, "action": action}


async def get_rain24(lat: float, lon: float) -> dict:
    now = datetime.now(timezone.utc)
    unavailable = {"available": False, "windows": [], "total_inches": None, "wettest_window": None, "pop_hourly": [],
                   "max_pop_pct": None, "action": {"show": False, "text": None, "window_start": None},
                   "source": SOURCE, "source_url": SOURCE_URL, "note": NOTE,
                   "warnings": ["Rain forecast unavailable right now; check weather.gov"]}
    pt = await get_json(f"{NWS}/points/{lat:.4f},{lon:.4f}", ttl=86400)
    try:
        p = pt["properties"]
        grid_url, hourly_url = p["forecastGridData"], p["forecastHourly"]
    except Exception:
        return freshness.with_meta(unavailable, source=SOURCE, freshness="cached", as_of=None)
    grid = await get_json(grid_url, ttl=TTL)
    hourly = await get_json(hourly_url, ttl=TTL)
    if not isinstance(grid, dict) or "properties" not in grid:
        return freshness.with_meta(unavailable, source=SOURCE, freshness="cached", as_of=None)
    out = build(parse_qpf(grid, now), parse_pop(hourly, now))
    out.update({"available": True, "source": SOURCE, "source_url": SOURCE_URL, "note": NOTE, "pop_available": hourly is not None})
    if hourly is None:
        out["warnings"] = ["Hourly chance of rain unavailable right now"]
    return freshness.with_meta(out, source=SOURCE, freshness="live", as_of=grid["properties"].get("updateTime"),
                               storm=out["action"]["show"] or freshness.storm_on())
