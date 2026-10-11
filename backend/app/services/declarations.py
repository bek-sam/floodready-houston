"""FEMA disaster declaration status for a county (OpenFEMA, no key)."""
from datetime import date, datetime, timezone

from app.services.http import get_json

URL = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
SOURCE = "https://www.fema.gov/about/openfema/data-sets"
TTL = 6 * 3600
ACTIVE_DAYS = 60
FIELDS = "disasterNumber,declarationTitle,declarationDate,incidentType,incidentBeginDate,incidentEndDate,ihProgramDeclared,iaProgramDeclared"
NOTE = ("Individuals can apply only for declared disasters. FEMA's page lists the registration deadline per disaster; "
        "confirm at DisasterAssistance.gov. Not official guidance. Call 911 for emergencies.")


def _d(s):
    return s[:10] if isinstance(s, str) and s else None


def _row(r: dict) -> dict:
    n = r.get("disasterNumber")
    return {"disaster_number": n, "title": r.get("declarationTitle"), "incident_type": r.get("incidentType"),
            "declaration_date": _d(r.get("declarationDate")), "incident_begin": _d(r.get("incidentBeginDate")),
            "incident_end": _d(r.get("incidentEndDate")), "ia_program": bool(r.get("iaProgramDeclared")),
            "ha_program": bool(r.get("ihProgramDeclared")), "url": f"https://www.fema.gov/disaster/{n}"}


def _is_active(row: dict, today: date) -> bool:
    if not (row["ia_program"] or row["ha_program"]):  # Beryl: IH true, IA false; individuals can still apply
        return False
    end = row["incident_end"]
    if not end:
        return True
    try:
        return (today - date.fromisoformat(end)).days <= ACTIVE_DAYS
    except ValueError:
        return False


async def status(county: str = "Harris", state: str = "TX") -> dict:
    county, state = county.strip(), state.strip().upper()
    base = {"available": False, "county": county, "state": state, "latest": None, "active_ia": False,
            "recent": [], "source": SOURCE, "note": NOTE}
    area = county if county.endswith("(County)") else f"{county} (County)"
    safe = lambda s: s.replace("'", "''")
    data = await get_json(URL, params={
        "$filter": f"state eq '{safe(state)}' and designatedArea eq '{safe(area)}'",
        "$orderby": "declarationDate desc", "$top": "25", "$select": FIELDS}, ttl=TTL)
    rows = data.get("DisasterDeclarationsSummaries") if isinstance(data, dict) else None
    if rows is None:
        base["warnings"] = ["FEMA declaration data is unavailable right now. Check DisasterAssistance.gov."]
        return base
    seen, recent = set(), []
    for r in rows:  # one row per county per disaster, but dedupe defensively
        row = _row(r)
        if row["disaster_number"] in seen:
            continue
        seen.add(row["disaster_number"])
        recent.append(row)
    today = datetime.now(timezone.utc).date()
    active = next((r for r in recent if _is_active(r, today)), None)
    base.update(available=True, latest=recent[0] if recent else None, recent=recent[:5], active_ia=active is not None)
    return base
