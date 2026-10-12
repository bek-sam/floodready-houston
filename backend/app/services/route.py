"""Route safety check: OSRM route + crossings near it + live conditions."""
from app.services import diskcache
from app.services.codes import reason_code, tag_warnings
from app.services.alerts import get_alerts, is_flood_alert, route_warnings
from app.services.data import haversine_m, load_json
from app.services.gauges import nearest_gauges
from app.services.http import get_json

OSRM = "https://router.project-osrm.org/route/v1/driving/{a},{b};{c},{d}"
BUFFER_M = 75
REPORT_BUFFER_M = 100
HIGH_DEPTH_IN = 6
REPORT_MAX_AGE_H = 6
LOW_PLAUSIBILITY = 0.3  # optional Jev report check (null = not checked)
COUNTING_KINDS = {"flooded_road", "water_over_road", "barricade_missing", "stalled_vehicles"}


def report_counts(kind, depth_in) -> bool:
    """A report only counts toward route hazards if its kind is known and depth is unknown or > 0."""
    return kind in COUNTING_KINDS and (depth_in is None or depth_in > 0)


CLEAR_MIN_VOTES = 3  # distinct clients saying "cleared" before a report stops counting as a hazard


def vote_counts(session, ids: list[str]) -> dict[str, dict]:
    """{report_id: {confirms, clears, last_vote_at}} from the report_votes table (missing ids -> zeros).
    Each client (voter hash) counts once per report: its latest vote wins."""
    out: dict[str, dict] = {}
    if not ids:
        return out
    from app.db import ReportVote
    latest: dict[tuple, object] = {}
    for v in session.query(ReportVote).filter(ReportVote.report_id.in_(ids)).order_by(ReportVote.id).all():
        latest[(v.report_id, v.voter or f"row-{v.id}")] = v
    for v in latest.values():
        c = out.setdefault(v.report_id, {"confirms": 0, "clears": 0, "last_vote_at": None})
        c["confirms" if v.still_there else "clears"] += 1
        ts = v.created_at.isoformat() if v.created_at else None
        if ts and (c["last_vote_at"] is None or ts > c["last_vote_at"]):
            c["last_vote_at"] = ts
    return out


def is_cleared(counts: dict | None) -> bool:
    c = counts or {}
    return c.get("clears", 0) >= CLEAR_MIN_VOTES and c.get("clears", 0) > c.get("confirms", 0)


def recent_reports() -> list[dict]:
    """Counting community reports from the last REPORT_MAX_AGE_H hours (empty list if the DB is unavailable)."""
    from datetime import datetime, timedelta, timezone
    try:
        from app.db import Report, get_session
        cutoff = datetime.now(timezone.utc) - timedelta(hours=REPORT_MAX_AGE_H)
        with get_session() as s:
            rows = s.query(Report).order_by(Report.created_at.desc()).limit(500).all()
            votes = vote_counts(s, [r.id for r in rows])
            out = []
            for r in rows:
                ts = r.created_at
                if ts is None:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                vc = votes.get(r.id) or {"confirms": 0, "clears": 0, "last_vote_at": None}
                if ts >= cutoff and report_counts(r.kind, r.depth_in) and not is_cleared(vc):
                    out.append({"id": r.id, "confirms": vc["confirms"], "clears": vc["clears"], "lat": r.lat, "lon": r.lon, "kind": r.kind, "depth_in": r.depth_in,
                                "note": r.note, "plausibility": r.plausibility, "created_at": ts.isoformat(),
                                "reporter": r.reporter})
            return out
    except Exception:
        return []


def load_crossings() -> list[dict]:
    d = load_json("crossings.geojson", {}) or {}
    return d.get("features", [])


def _names(hazards: list[dict]) -> str:
    names = [(h["name"] or "unnamed")[:80] for h in hazards]
    txt = ", ".join(names[:3])
    return txt + (f" +{len(names) - 3} more" if len(names) > 3 else "")


def _min_dist_m(lat, lon, coords) -> float:
    # coords are [lon, lat]; check vertices plus midpoints (route vertices are dense with overview=full)
    best = 1e12
    prev = None
    for x, y in coords:
        best = min(best, haversine_m(lat, lon, y, x))
        if prev:
            best = min(best, haversine_m(lat, lon, (y + prev[1]) / 2, (x + prev[0]) / 2))
        prev = (x, y)
    return best


async def check_route(origin: dict, destination: dict, simulate: bool = False) -> dict:
    warnings = []
    o, d = origin, destination
    url = OSRM.format(a=o["lon"], b=o["lat"], c=d["lon"], d=d["lat"])
    rkey = f"{o['lat']:.4f},{o['lon']:.4f};{d['lat']:.4f},{d['lon']:.4f}"
    data = diskcache.get("routes", rkey)
    if not data or len(data.get("routes") or []) < 2:  # older cache entries have no alternatives; refresh once
        fresh = await get_json(url, {"overview": "full", "geometries": "geojson", "alternatives": "true"}, ttl=600)
        if fresh and fresh.get("routes"):
            data = fresh
            diskcache.put("routes", rkey, data)
    fallback = False
    try:
        line = data["routes"][0]["geometry"]
    except Exception:
        fallback = True
        warnings.append("Routing service unavailable; showing a straight line, not a real route")
        line = {"type": "LineString", "coordinates": [[o["lon"], o["lat"]], [d["lon"], d["lat"]]]}
    out = await _evaluate(line, fallback, simulate, warnings)
    if not fallback and out["verdict"] in ("avoid", "caution") and out["hazards"]:
        try:
            best = None
            for r in (data.get("routes") or [])[1:3]:
                alt = await _evaluate(r["geometry"], False, simulate, [])
                if len(alt["hazards"]) < len(out["hazards"]) and (best is None or len(alt["hazards"]) < len(best[0]["hazards"])):
                    best = (alt, r)
            if best:
                alt, r = best
                p0 = data["routes"][0]
                dmin = max(0.0, (r["duration"] - p0["duration"]) / 60)
                dmi = max(0.0, (r["distance"] - p0["distance"]) / 1609.344)
                out["alternative"] = {"route": alt["route"], "hazards": alt["hazards"], "hazard_count": len(alt["hazards"]),
                                      "verdict": alt["verdict"], "message": alt["message"],
                                      "extra_min": round(dmin, 1), "extra_mi": round(dmi, 1), "message_code": "route.alt"}
        except Exception:
            pass
    return out


async def _evaluate(line: dict, fallback: bool, simulate: bool, warnings: list) -> dict:
    coords = line["coordinates"]

    hazards, high, deep_report = [], False, None
    deep_ids: set = set()
    rep_ids: set = set()
    for f in load_crossings():
        try:
            lon, lat = f["geometry"]["coordinates"][:2]
        except Exception:
            continue
        if _min_dist_m(lat, lon, coords) <= BUFFER_M:
            p = f.get("properties", {})
            reasons = p.get("reasons") or []
            rtxt = reasons[0] if reasons else "Known flood-prone crossing"
            rc = reason_code(rtxt)
            hazards.append({"crossing_id": p.get("id"), "name": p.get("short_name") or p.get("name"), "lat": lat, "lon": lon,
                            "reason": rtxt, "reason_code": rc[0] if rc else None, "reason_params": rc[1] if rc else {}})
            high = high or p.get("risk") == "high"

    # counting community reports (<= 6 h old) within 100 m of the route
    for rep in recent_reports():
        if _min_dist_m(rep["lat"], rep["lon"], coords) <= REPORT_BUFFER_M:
            depth = rep.get("depth_in")
            hazards.append({"kind": "report", "crossing_id": None, "name": "Community report", "lat": rep["lat"],
                            "lon": rep["lon"], "depth_in": depth, "report_kind": rep.get("kind"),
                            "reported_at": rep.get("created_at"),
                            "name_code": "route.rep.name",
                            "reason_code": ("route.rep.dn" if rep.get("note") else "route.rep.d") if depth is not None
                            else ("route.rep.n" if rep.get("note") else "route.rep"),
                            "reason_params": {"depth": f"{depth:g}" if depth is not None else "", "note": rep.get("note") or ""},
                            "report_id": rep.get("id"), "confirms": rep.get("confirms", 0), "clears": rep.get("clears", 0),
                            "reason": "Community report" + (f": about {depth:g} in of water" if depth is not None else "")
                            + (f" ({rep['note']})" if rep.get("note") else "")})
            if rep.get("plausibility") is not None and rep["plausibility"] < LOW_PLAUSIBILITY:
                continue  # Jev judged it implausible: still shown, but never counts toward "avoid"
            rep_ids.add(rep.get("reporter") or rep.get("id"))  # one client filing twice counts once
            if depth is not None and depth >= HIGH_DEPTH_IN:
                deep_ids.add(rep.get("reporter") or rep.get("id"))
                deep_report = depth
    # Anonymous reports are unverified: one report can raise a route to "caution" at most.
    # It takes reports from >= 2 distinct clients (at least one deep) to count as evidence of active flooding.
    if deep_report is not None and len(rep_ids) >= 2:
        high = True
    else:
        deep_report = None

    # live conditions near the route midpoint
    mid = coords[len(coords) // 2]
    active, conds, cond_codes = simulate, [], []
    if simulate:
        conds.append("simulated storm")
        cond_codes.append({"code": "route.c.sim", "params": {}})
    al = await get_alerts(mid[1], mid[0])
    fl = [a for a in al["alerts"] if is_flood_alert(a)]
    if fl:
        active = True
        conds.append(fl[0]["event"])
        cond_codes.append({"code": "route.c.event", "params": {"event": fl[0]["event"]}})
    if al.get("warnings"):
        warnings += al["warnings"]
    if deep_report is not None:  # a fresh deep-water report is itself evidence of active flooding
        active = True
        conds.append(f"community report of {deep_report:g} in of water")
        cond_codes.append({"code": "route.c.report", "params": {"depth": f"{deep_report:g}"}})
    if hazards:
        for g in await nearest_gauges(mid[1], mid[0], 3, simulate):
            if g["status"] in ("action", "minor", "moderate", "major"):
                active = True
                conds.append(f"{g['name']} gauge at {g['status']} stage")
                cond_codes.append({"code": "route.c.gauge", "params": {"name": g["name"], "status": g["status"]}})
                break

    wl = []
    try:
        wl = await route_warnings(coords)
    except Exception:
        pass
    if wl:
        active = True
        conds.append(wl[0]["event"])
        cond_codes.append({"code": "route.c.warning", "params": {"event": wl[0]["event"]}})

    if hazards and high and active:
        verdict, mcode, mparams = "avoid", "route.avoid", {"n": len(hazards)}
        msg = (f"Avoid this route. It passes {len(hazards)} flood-prone crossing(s) "
               f"({_names(hazards)}) and conditions are active ({'; '.join(conds)}). "
               "Turn around, don't drown. Call 911 if you are in danger.")
    elif hazards and simulate and active:
        verdict, mcode, mparams = "caution", "route.cautionSim", {"n": len(hazards), "conditions": "; ".join(conds)}
        msg = (f"Use caution. This route crosses {len(hazards)} known flood-prone spot(s) "
               f"({_names(hazards)}). Simulated storm: conditions are active ({'; '.join(conds)}). "
               "This is a demo, not a real route verdict. Turn around, don't drown.")
    elif hazards and all(h.get("kind") == "report" for h in hazards) and len(hazards) == 1:
        verdict, mcode, mparams = "caution", "route.cautionReport", {}
        msg = ("Use caution. One unverified community report of water on this route. "
               "A single report cannot confirm flooding; check alerts and never drive into water.")
    elif hazards:
        verdict, mcode, mparams = "caution", "route.caution", {"n": len(hazards)}
        msg = (f"Use caution. This route crosses {len(hazards)} known flood-prone spot(s) "
               f"({_names(hazards)}). No active flood conditions detected right now, "
               "but check alerts before you go in rain.")
    elif fallback:
        verdict, mcode, mparams = "caution", "route.fallback", {}
        msg = "Route unavailable, check manually. We could not get a real driving route, so no flood check was possible. Never drive through floodwater."
    else:
        verdict, mcode, mparams = "safe", "route.safe", {}
        msg = "No known flood-prone crossings on this route — conditions can change fast; never drive into water."
    if wl:
        ev = wl[0]["event"]
        if verdict == "safe":
            verdict, mcode, mparams = "caution", "route.warning", {"event": ev}
            msg = (f"Use caution. A {ev} is in effect along this route"
                   + (f" ({wl[0]['headline']})" if wl[0].get("headline") else "")
                   + ". Do not drive through water. Turn around, don't drown. Call 911 if you are in danger.")
        else:
            msg += f" An active {ev} also covers part of this route."
    n_rep = sum(1 for h in hazards if h.get("kind") == "report")
    if n_rep:
        msg += f" {n_rep} community report{'s' if n_rep != 1 else ''} on this route in the last 6 hours."
    out = {"route": line, "hazards": hazards, "verdict": verdict, "message": msg, "report_count": n_rep,
           "message_code": mcode, "message_params": mparams, "conditions": cond_codes}
    if wl:
        out["active_warnings"] = [{"event": w["event"], "headline": w.get("headline"), "expires": w.get("expires")} for w in wl]
    if warnings:
        out["warnings"] = warnings
        tag_warnings(out)
    return out


# Pre-seeded demo routes (OSRM results are cached in backend/.cache/routes.json).
DEMO_ROUTES = [
    {"label": "Downtown: Allen Parkway underpass", "origin": {"lat": 29.7648, "lon": -95.3665}, "destination": {"lat": 29.7648, "lon": -95.3560}},
    {"label": "UH campus to Downtown", "origin": {"lat": 29.7199, "lon": -95.3422}, "destination": {"lat": 29.7607, "lon": -95.3695}},
    {"label": "Meyerland to Downtown", "origin": {"lat": 29.6786, "lon": -95.4640}, "destination": {"lat": 29.7607, "lon": -95.3695}},
    {"label": "Meyerland to UH campus", "origin": {"lat": 29.6786, "lon": -95.4640}, "destination": {"lat": 29.7199, "lon": -95.3422}},
]
