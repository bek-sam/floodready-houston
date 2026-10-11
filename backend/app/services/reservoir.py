"""Addicks pool level (NWPS ADDT2) compared with the ground elevation at a point."""
import asyncio
import json

from app import freshness
from app.config import DATA_DIR
from app.services import risk as risk_svc
from app.services.http import get_json

URL = "https://api.water.noaa.gov/nwps/v1/gauges/ADDT2"
SOURCE = "https://water.noaa.gov/gauges/ADDT2"
HARVEY_CREST_FT = 109.09
HARVEY_CREST_DATE = "2017-08-30"
DATUM_NOTE = ("Pool and ground elevations may use different vertical datums (NGVD29 vs NAVD88); "
              "treat as approximate.")
DISCLAIMER = "Not official guidance. Call 911 and follow evacuation orders."
NEAR_FT = 15.0


def _static_stages() -> tuple[float, float]:
    try:
        for g in json.loads((DATA_DIR / "gauges.json").read_text()):
            if g.get("id") == "ADDT2":
                fs = g["flood_stages"]
                return float(fs["action"]), float(fs["minor"])
    except Exception:
        pass
    return 93.0, 96.0


def _status(stage, action, minor) -> str:
    if stage is None:
        return "unknown"
    return "minor" if stage >= minor else "action" if stage >= action else "normal"


async def get_pool(lat: float, lon: float) -> dict:
    d, elev_raw, res = await asyncio.gather(
        get_json(URL, ttl=300), risk_svc._elev(lat, lon), risk_svc.reservoir_status(lat, lon),
        return_exceptions=True)
    ground = None
    try:
        v = float(elev_raw["value"])
        if v > -1000:
            ground = round(v, 1)
    except Exception:
        pass
    in_area = bool(res.get("in_area")) if isinstance(res, dict) else False
    action, minor = _static_stages()
    stage = observed = None
    try:
        stage = float(d["status"]["observed"]["primary"])
        observed = d["status"]["observed"].get("validTime")
        cats = d["flood"]["categories"]
        action = float(cats["action"]["stage"]) if cats["action"].get("stage") else action
        minor = float(cats["minor"]["stage"]) if cats["minor"].get("stage") else minor
        if stage < -900:
            stage = None
    except Exception:
        stage = None
    out = {"ground_elevation_ft": ground, "pool_below_ground_ft": None, "harvey_above_ground_ft": None,
           "relevant": False, "datum_note": DATUM_NOTE, "disclaimer": DISCLAIMER, "barker": None, "source": SOURCE}
    if stage is None:
        out.update(available=False, pool=None, message="Live pool level unavailable",
                   message_code="res.pool.unavailable",
                   meta=freshness.meta(SOURCE, "snapshot"),
                   warnings=["NOAA NWPS unavailable; showing static flood-stage thresholds only"],
                   thresholds={"action_ft": action, "minor_ft": minor, "harvey_crest_ft": HARVEY_CREST_FT})
        if ground is not None:
            out["harvey_above_ground_ft"] = round(HARVEY_CREST_FT - ground, 1)
        return out
    status = _status(stage, action, minor)
    out["available"] = True
    out["pool"] = {"gauge_id": "ADDT2", "name": "Addicks Reservoir pool", "stage_ft": round(stage, 2),
                   "observed_at": observed, "action_ft": action, "minor_ft": minor,
                   "harvey_crest_ft": HARVEY_CREST_FT, "harvey_crest_date": HARVEY_CREST_DATE, "status": status}
    if ground is not None:
        out["pool_below_ground_ft"] = round(ground - stage, 1)
        out["harvey_above_ground_ft"] = round(HARVEY_CREST_FT - ground, 1)
    near = ground is not None and ground - stage <= NEAR_FT
    out["relevant"] = bool(in_area and (near or stage >= action))
    if ground is None:
        out["message"], out["message_code"] = f"Addicks pool is at {stage:.1f} ft.", "res.pool.noground"
    elif ground >= stage:
        out["message"] = (f"Addicks pool is {ground - stage:.1f} ft below your ground. "
                          f"Harvey's crest was {HARVEY_CREST_FT - ground:.1f} ft above it.")
        out["message_code"] = "res.pool.below"
    else:
        out["message"], out["message_code"] = f"Addicks pool is {stage - ground:.1f} ft above your ground.", "res.pool.above"
    out["meta"] = freshness.meta(SOURCE, "live", as_of=observed)
    return out
