"""NFIP claims/policies by ZIP from OpenFEMA (no key). v3 'NfipClaims' replaces deprecated v2 'FimaNfipClaims'."""
import logging
import re
import time
import statistics
from collections import Counter
from datetime import date

from app.services import diskcache
from app.services.codes import tag_warnings
from app.services.http import get_json

log = logging.getLogger("zipinsurance")
BASE = "https://www.fema.gov/api/open"
SOURCE = "https://www.fema.gov/openfema-data-page/nfip-redacted-claims-v3"
TTL = 24 * 3600
SHORT_TTL = 300
SEED_ZIPS = ["77096", "77004", "77002", "77026"]
NOTE = ("Counts are NFIP flood-insurance claims filed in this ZIP (redacted OpenFEMA data); uninsured flood damage "
        "is not included. Policies in force is an approximate count of policy records active today.")
_mem: dict = {}


def _out(d: dict) -> dict:
    o = {k: v for k, v in d.items() if k != "fetched_at"}
    o.setdefault("premiums", None)
    return o


def valid_zip(z: str) -> bool:
    return isinstance(z, str) and bool(re.fullmatch(r"[0-9]{5}", z))


async def _claims(z: str):
    """Returns list of years or None on failure. One small $select query (yearOfLoss only)."""
    years: list = []
    for ent, ver, key in (("NfipClaims", "v3", "NfipClaims"), ("FimaNfipClaims", "v2", "FimaNfipClaims")):
        years, ok = [], True
        for skip in (0, 10000, 20000):  # ZIPs have a few thousand claims at most; cap pages
            d = await get_json(f"{BASE}/{ver}/{ent}", {
                "$filter": f"reportedZipCode eq '{z}'", "$select": "yearOfLoss", "$top": 10000, "$skip": skip},
                ttl=TTL)
            rows = (d or {}).get(key) if isinstance(d, dict) else None
            if rows is None:
                ok = False
                break
            years += [r.get("yearOfLoss") for r in rows]
            if len(rows) < 10000:
                break
        if ok:
            return years
    return None


async def _policies(z: str):
    today = f"{date.today().isoformat()}T00:00:00.000Z"
    for _ in range(2):  # one retry: OpenFEMA occasionally times out on count queries
        d = await get_json(f"{BASE}/v3/NfipPolicies", {
            "$filter": f"reportedZipCode eq '{z}' and policyEffectiveDate le '{today}' and policyTerminationDate ge '{today}'",
            "$select": "reportedZipCode", "$top": 1, "$count": "true"}, ttl=TTL)
        try:
            c = d["metadata"]["count"]
            if isinstance(c, int) and c > 0:
                return c
        except Exception:
            pass
    return None


async def _premiums(z: str):
    """Annual premium distribution of in-force policies (OpenFEMA totalInsurancePremiumOfThePolicy). None on failure."""
    today = f"{date.today().isoformat()}T00:00:00.000Z"
    d = await get_json(f"{BASE}/v3/NfipPolicies", {
        "$filter": f"reportedZipCode eq '{z}' and policyEffectiveDate le '{today}' and policyTerminationDate ge '{today}'",
        "$select": "totalInsurancePremiumOfThePolicy", "$top": 10000}, ttl=TTL)
    try:
        rows = d["NfipPolicies"]
        truncated = len(rows) >= 10000
        vals = [r["totalInsurancePremiumOfThePolicy"] for r in rows]
        vals = sorted(v for v in vals if isinstance(v, (int, float)) and v > 0)
        if not vals:
            return None
        q = statistics.quantiles(vals, n=4) if len(vals) >= 2 else [vals[0]] * 3
        return {"median_annual": round(q[1]), "p25": round(q[0]), "p75": round(q[2]), "sample_size": len(vals),
                "truncated": truncated,
                "source": "https://www.fema.gov/openfema-data-page/nfip-redacted-policies-v3"}
    except Exception:
        return None


async def fetch_zip(z: str) -> dict | None:
    years = await _claims(z)
    if years is None:
        return None
    cnt = Counter(y for y in years if isinstance(y, int))
    by_year = [{"year": y, "count": cnt[y]} for y in sorted(cnt)]
    policies, premiums = await _policies(z), await _premiums(z)
    if policies is None and premiums and not premiums.get("truncated"):
        policies = premiums["sample_size"]  # same in-force filter; sample is the full set when under the 10,000 page cap
    return {"zip": z,
            "claims": {"total": sum(cnt.values()), "since_2017": sum(c for y, c in cnt.items() if y >= 2017),
                       "by_year": by_year},
            "policies_in_force": policies, "premiums": premiums, "source": SOURCE, "note": NOTE, "note_code": "zip.note",
            "fetched_at": time.time()}


async def zip_insurance(z: str) -> dict:
    if not valid_zip(z):  # z goes into an OData $filter: never trust callers (AI tools, other services)
        raise ValueError("zip must be 5 digits")
    hit = _mem.get(z)
    if hit and time.time() - hit["fetched_at"] < TTL:
        return _out(hit)
    snap = diskcache.get("zip_insurance", z)
    if snap and snap.get("premiums") is not None and snap.get("policies_in_force") is not None and time.time() - snap.get("fetched_at", 0) < TTL:
        _mem[z] = snap
        return _out(snap)
    fresh = await fetch_zip(z)
    if fresh:
        if fresh.get("premiums") is not None and fresh.get("policies_in_force") is not None:
            _mem[z] = fresh
            diskcache.put("zip_insurance", z, fresh)
            return _out(fresh)
        # policy/premium calls partly failed: short TTL, never poison the 24 h cache (memory or disk)
        _mem[z] = {**fresh, "fetched_at": time.time() - TTL + SHORT_TTL}
        out = _out(fresh)
        out["warnings"] = ["Policy and premium data temporarily unavailable; claims shown."]
        return tag_warnings(out)
    if snap:  # stale disk snapshot beats nothing
        out = _out(snap)
        out["warnings"] = ["OpenFEMA unavailable; showing a saved snapshot"]
        tag_warnings(out)
        return out
    return tag_warnings({"zip": z, "claims": {"total": 0, "since_2017": 0, "by_year": []}, "policies_in_force": None,
                         "premiums": None, "source": SOURCE, "note": NOTE, "note_code": "zip.note",
                         "warnings": ["OpenFEMA unavailable; no claims data. Zero here means unknown, not safe."]})


async def preseed():
    for z in SEED_ZIPS:
        try:
            await zip_insurance(z)
        except Exception as e:
            log.warning("preseed %s failed: %s", z, e)
