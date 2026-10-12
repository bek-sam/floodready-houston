import asyncio

from app.services.data import haversine_m, load_json

SOURCE = "https://data.cms.gov/provider-data/topics/dialysis-facilities"
KINDS = {"dialysis": "dialysis.json"}


async def nearby(lat: float, lon: float, kind: str = "dialysis", limit: int = 5) -> dict:
    fname = KINDS.get(kind)
    if not fname:
        return {"facilities": [], "source": SOURCE, "note": f"Unknown kind '{kind}'. Supported: {', '.join(KINDS)}."}
    rows = load_json(fname, None)
    if not isinstance(rows, list):
        rows = (rows or {}).get("facilities") if isinstance(rows, dict) else None
    if not rows:
        return {"facilities": [], "source": SOURCE,
                "note": "Dialysis facility list is not available yet. Call your clinic directly and ask about their storm plan."}
    out = []
    for r in rows:
        try:
            d = haversine_m(lat, lon, float(r["lat"]), float(r["lon"])) / 1609.344
        except Exception:
            continue
        addr = ", ".join(str(x) for x in (r.get("address"), r.get("city"), r.get("zip")) if x)
        out.append({"name": r.get("name"), "address": addr, "phone": r.get("phone"),
                    "lat": float(r["lat"]), "lon": float(r["lon"]), "distance_mi": round(d, 1)})
    out.sort(key=lambda f: f["distance_mi"])
    top = out[:max(1, min(limit, 25))]
    await asyncio.gather(*(_exposure(f) for f in top[:5]))  # exposure for nearest 5 only (cached HTTP)
    return {"facilities": top, "source": SOURCE, "exposure_source": FEMA_SOURCE,
            "note": "Distances are straight-line. Confirm hours and storm closures by phone before you go."}


FEMA_SOURCE = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28"


async def _exposure(f: dict) -> None:
    f.update({"fema_zone": None, "sfha": None, "harvey_flooded": None})
    try:
        from app.services.risk import _fema
        d = await _fema(f["lat"], f["lon"])
        a = ((d or {}).get("features") or [{}])[0].get("attributes") or {}
        f["fema_zone"] = a.get("FLD_ZONE")
        t = a.get("SFHA_TF")
        f["sfha"] = (t == "T") if t in ("T", "F") else None
    except Exception:
        pass
    try:
        from app.services.harvey import harvey_at
        f["harvey_flooded"] = (await asyncio.to_thread(harvey_at, f["lat"], f["lon"])).get("flooded")
    except Exception:
        pass
