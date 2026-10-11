"""FAA NAS closure list for Houston airports. Closures only: not weather, delays or ground stops."""
import time
import xml.etree.ElementTree as ET

import httpx

from app import freshness
from app.config import HTTP_TIMEOUT, USER_AGENT
from app.services import http as httpc

URL = "https://nasstatus.faa.gov/api/airport-status-information"
SOURCE = "https://nasstatus.faa.gov/"
CODES = ("IAH", "HOU")
TTL = 120


def parse(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    found = {}
    for a in root.iter("Airport"):
        code = (a.findtext("ARPT") or "").strip()
        if code in CODES:
            found[code] = {"code": code, "closed": True, "reason": (a.findtext("Reason") or "").strip() or None,
                           "reopen": (a.findtext("Reopen") or "").strip() or None}
    return [found.get(c, {"code": c, "closed": False, "reason": None, "reopen": None}) for c in CODES]


async def get_status() -> dict:
    key = ("airports", URL)
    airports = httpc.cache_get(key)
    if airports is None:
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True,
                                         headers={"User-Agent": USER_AGENT}) as c:
                r = await c.get(URL)
                r.raise_for_status()
                airports = parse(r.text)
            httpc.cache_set(key, airports, TTL)
            freshness.record("FAA NAS", True, 0)
        except Exception:
            return {"airports": [{"code": c, "closed": None, "reason": None, "reopen": None} for c in CODES],
                    "source": SOURCE, "meta": freshness.meta(SOURCE, "cached"),
                    "warnings": ["FAA status unavailable"]}
    return {"airports": airports, "source": SOURCE, "meta": freshness.meta(SOURCE, "live"),
            "note": "FAA lists closures only; it does not report weather or delays."}
