"""LangGraph tools wrapping backend services. Imports are lazy so the AI module works standalone."""
import asyncio
import importlib
import inspect
import json
import os
import sys
import time
from datetime import date

from langchain_core.tools import tool

from . import rag


def _plain(x):
    if hasattr(x, "model_dump"):
        return x.model_dump(mode="json")
    if isinstance(x, (list, tuple)):
        return [_plain(i) for i in x]
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, date):
        return x.isoformat()
    return x


async def _call(module: str, func: str, *args):
    try:
        fn = getattr(importlib.import_module(f"app.services.{module}"), func)
        r = fn(*args)
        if inspect.isawaitable(r):
            r = await r
        return _plain(r)
    except Exception:
        return {"error": "unavailable"}


@tool
async def get_risk(lat: float, lon: float, simulate: bool = False) -> dict:
    """Flood risk at a point: FEMA zone, elevation, nearby river gauges, jurisdiction, sourced facts.
    simulate=True uses simulated high-water gauge data for demos."""
    return await _call("risk", "get_risk", lat, lon, *([True] if simulate else []))


@tool
async def get_alerts(lat: float, lon: float) -> dict:
    """Active National Weather Service alerts at a point."""
    return await _call("alerts", "get_alerts", lat, lon)


@tool
async def check_route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float,
                      simulate: bool = False) -> dict:
    """Check a driving route for flood-prone crossings. Returns verdict safe|caution|avoid."""
    return await _call(
        "route", "check_route", {"lat": origin_lat, "lon": origin_lon}, {"lat": dest_lat, "lon": dest_lon},
        *([True] if simulate else []),
    )


@tool
async def insurance_countdown(purchase_date: str = "") -> dict:
    """NFIP flood insurance 30-day waiting period. purchase_date is YYYY-MM-DD (empty = today)."""
    return await _call("insurance", "insurance_countdown", purchase_date or None)


@tool
async def get_civic(lat: float, lon: float) -> dict:
    """Civic info at a point: flood bond projects, reservoir area, which agency is responsible."""
    return await _call("civic", "get_civic", lat, lon)


@tool
async def get_shelters(lat: float, lon: float, pet_friendly: bool = False, limit: int = 5) -> dict:
    """Nearest evacuation shelters with status (Open/Pending/Full/Closed). Only 'Open' shelters are open."""
    try:
        from app.services.shelters import get_shelters as svc
    except Exception:
        return {"error": "shelters unavailable"}
    try:
        return _plain(await svc(lat, lon, pet_friendly, limit))
    except Exception:
        return {"error": "unavailable"}


@tool
async def get_flood_history(lat: float, lon: float, zip: str = "") -> dict:
    """Did this place flood before? Harvey (2017) flooded flag plus past events with the nearest gauge's peak
    stage, and the ZIP's peak NFIP claims year if a ZIP is given."""
    return await _call("floodhistory", "flood_history", lat, lon, zip or None)


@tool
async def get_zip_insurance(zip: str) -> dict:
    """NFIP flood insurance claims (total, since 2017, by year) and policies in force for a 5-digit ZIP (OpenFEMA)."""
    return await _call("zipinsurance", "zip_insurance", zip)


@tool
async def get_medical(lat: float, lon: float, kind: str = "dialysis", limit: int = 3) -> dict:
    """Nearest medical facilities (dialysis centers) with address, phone and straight-line distance."""
    return await _call("medical", "nearby", lat, lon, kind, limit)


@tool
def search_knowledge(query: str) -> list:
    """Search the sourced flood knowledge base. Returns [{text, source, score}]."""
    return rag.search(query, 4)


ALL_TOOLS = [get_risk, get_alerts, check_route, insurance_countdown, get_civic, get_shelters, get_flood_history, get_zip_insurance,
             get_medical, search_knowledge]
TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}


# Short TTL cache for read-only service tools (seconds). Errors and "warnings" results are never cached.
TOOL_TTL = {"get_risk": 600, "get_alerts": 120, "get_flood_history": 3600, "get_zip_insurance": 6 * 3600,
            "get_civic": 3600, "get_shelters": 3600, "get_medical": 3600, "insurance_countdown": 600}
_tool_cache: dict[str, tuple[float, object]] = {}
_inflight: dict[str, asyncio.Future] = {}


def _cache_on() -> bool:
    return os.getenv("AI_TOOL_CACHE", "0" if "pytest" in sys.modules else "1") != "0"


def _tkey(name: str, args: dict) -> str:
    a = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in (args or {}).items()}  # ~100 m grid
    return name + json.dumps(a, sort_keys=True, default=str)


async def _invoke(t, args):
    try:
        return await t.ainvoke(args)
    except Exception:
        return {"error": "unavailable"}


async def run_tool(name: str, args: dict):
    t = TOOLS_BY_NAME.get(name)
    if t is None:
        return {"error": "unknown tool"}
    ttl = TOOL_TTL.get(name)
    if not ttl or not _cache_on():
        return await _invoke(t, args)
    k = _tkey(name, args)
    hit = _tool_cache.get(k)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    loop = asyncio.get_running_loop()
    if k in _inflight and _inflight[k].get_loop() is loop:  # same call already running (e.g. /ask/prefetch): share it
        return await asyncio.shield(_inflight[k])
    fut = loop.create_future()
    _inflight[k] = fut
    try:
        r = await _invoke(t, args)
        if not (isinstance(r, dict) and (r.get("error") or r.get("warnings"))):
            _tool_cache[k] = (time.time(), r)
        fut.set_result(r)
        return r
    except BaseException as e:
        fut.set_result({"error": "unavailable"})
        raise e
    finally:
        _inflight.pop(k, None)


async def warm(lat: float, lon: float) -> list[str]:
    """Prefetch the location tools the Ask page will most likely need."""
    names = ["get_risk", "get_flood_history", "get_alerts"]
    await asyncio.gather(*[run_tool(n, {"lat": lat, "lon": lon, **({"zip": ""} if n == "get_flood_history" else {})}) for n in names])
    return names
