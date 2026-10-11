"""Re-fetch the snapshot datasets, diff against what is in data/, write data/snapshots/manifest.json.

  cd backend && uv run python ../scripts/refresh_snapshots.py --dry-run        # fetch + diff, change nothing
  cd backend && uv run python ../scripts/refresh_snapshots.py --manifest-only  # just record current dates/counts
  cd backend && uv run python ../scripts/refresh_snapshots.py                  # apply (crossings + dialysis re-run their slow fetch scripts)

Datasets: shelters (ArcGIS), bond layers (HCFCD ArcGIS), dialysis (CMS), crossings (fetch_crossings_extra.py).
Never crashes the app: it only touches data/ files and the manifest.
"""
import argparse, json, shutil, subprocess, sys, time
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAP = DATA / "snapshots"
UA = {"User-Agent": "FloodReadyHouston/0.1 (hackathon)"}
SHELTERS = "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Evacuation_Shelters/FeatureServer/0"
HCFCD = "https://services2.arcgis.com/nLl0k0Mja5hnSeSl/arcgis/rest/services"
BOND = f"{HCFCD}/Bond_CIP_Structural_CJO/FeatureServer/0"
CMS = "https://data.cms.gov/provider-data/api/1/datastore/query/23ew-n7w9/0"
SOURCES = {"shelters": SHELTERS, "bond": BOND, "dialysis": "https://data.cms.gov/provider-data/dataset/23ew-n7w9",
           "crossings": "https://www.click2houston.com/ + USGS STN + OpenStreetMap (see fetch_crossings_extra.py)",
           "harvey": "https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4"}


def get(url, params):
    return httpx.get(url, params=params, timeout=60, headers=UA, follow_redirects=True).json()


def diff(old: dict, new: dict) -> dict:
    """old/new: key -> comparable value."""
    added = [k for k in new if k not in old]
    removed = [k for k in old if k not in new]
    changed = [k for k in new if k in old and new[k] != old[k]]
    return {"added": len(added), "removed": len(removed), "changed": len(changed),
            "examples": {"added": added[:3], "removed": removed[:3], "changed": changed[:3]}}


def feats_index(feats, keyf):
    out = {}
    for f in feats:
        p = f.get("properties") or {}
        out[keyf(p)] = json.dumps({k: p.get(k) for k in sorted(p) if k not in ("EditDate", "OBJECTID")}, sort_keys=True, default=str)
    return out


def load(rel, default):
    try:
        return json.loads((DATA / rel).read_text())
    except Exception:
        return default


def fetch_layer(url):
    d = get(url + "/query", {"where": "1=1", "outFields": "*", "f": "geojson", "outSR": 4326, "resultRecordCount": 2000})
    if not d.get("features"):
        raise RuntimeError("no features returned")
    return d


def do_shelters(apply):
    new = fetch_layer(SHELTERS)
    cur = load("shelters.json", {}).get("features", [])
    key = lambda p: f'{p.get("Name")}|{p.get("Address")}'
    rep = diff(feats_index(cur, key), feats_index(new["features"], key))
    if apply:
        (DATA / "shelters.json").write_text(json.dumps(new))
    return rep, len(new["features"])


def do_bond(apply):
    new = fetch_layer(BOND)
    cur = load("snapshots/bond.json", {}).get("features", [])
    key = lambda p: str(p.get("Project_Title") or p.get("PROJECT_ID") or p.get("Project_ID"))
    rep = diff(feats_index(cur, key), feats_index(new["features"], key))
    if apply:
        SNAP.mkdir(parents=True, exist_ok=True)
        (SNAP / "bond.json").write_text(json.dumps(new))
    return rep, len(new["features"])


def do_dialysis(apply):
    rows, off = [], 0
    while True:
        r = get(CMS, {"limit": 500, "offset": off, "conditions[0][property]": "state", "conditions[0][value]": "TX",
                      "conditions[1][property]": "countyparish", "conditions[1][value]": "Harris"})["results"]
        rows += r
        if len(r) < 500:
            break
        off += 500
    new = {f'{x["facility_name"].title()}|{x["address_line_1"].title()}': x.get("telephone_number") for x in rows}
    cur = {f'{x["name"]}|{x["address"]}': x.get("phone") for x in load("dialysis.json", [])}
    rep = diff(cur, new)  # cur lacks facilities the geocoder could not place, so 'added' may include those
    if apply:
        run_script("fetch_dialysis.py")
    return rep, len(new)


def do_crossings(apply):
    path = DATA / "crossings.geojson"
    before = {f["properties"].get("id"): json.dumps(f["properties"], sort_keys=True) for f in load("crossings.geojson", {}).get("features", [])}
    if not apply:
        return {"added": None, "removed": None, "changed": None,
                "note": "skipped in --dry-run (re-fetch is slow and rewrites the file); run without --dry-run"}, len(before)
    backup = path.with_suffix(".bak")
    shutil.copy(path, backup)
    run_script("fetch_crossings_extra.py")
    after = {f["properties"].get("id"): json.dumps(f["properties"], sort_keys=True) for f in load("crossings.geojson", {}).get("features", [])}
    return diff(before, after), len(after)


def run_script(name):
    subprocess.run([sys.executable, str(ROOT / "scripts" / name)], check=True, cwd=ROOT / "backend")


def current_counts():
    return {"shelters": len(load("shelters.json", {}).get("features", [])),
            "bond": len(load("snapshots/bond.json", {}).get("features", [])),
            "dialysis": len(load("dialysis.json", [])),
            "crossings": len(load("crossings.geojson", {}).get("features", [])),
            "harvey": load("harvey/coverage.json", {}).get("features_stored"),
            "knowledge": len(list((DATA / "knowledge").glob("*.md")))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="fetch and diff only; write nothing")
    ap.add_argument("--manifest-only", action="store_true", help="record current dates/counts without fetching")
    ap.add_argument("--only", help="comma list: shelters,bond,dialysis,crossings")
    a = ap.parse_args()
    today = date.today().isoformat()
    man_path = SNAP / "manifest.json"
    man = load("snapshots/manifest.json", {"snapshots": {}})
    snaps = man.setdefault("snapshots", {})
    counts = current_counts()
    report = {}
    if a.manifest_only:
        for k, n in counts.items():
            fp = {"shelters": "shelters.json", "bond": "snapshots/bond.json", "dialysis": "dialysis.json",
                  "crossings": "crossings.geojson", "harvey": "harvey/coverage.json", "knowledge": "knowledge"}[k]
            p = DATA / fp
            if not p.exists():
                continue
            if k == "knowledge":
                ts = max(f.stat().st_mtime for f in p.glob("*.md"))
            elif k == "harvey":
                ts = datetime.fromisoformat(load(fp, {}).get("fetched_at", "").replace("Z", "+00:00")).timestamp()
            else:
                ts = p.stat().st_mtime
            snaps[k] = {"date": datetime.fromtimestamp(ts, timezone.utc).date().isoformat(), "count": n, "source": SOURCES.get(k)}
    else:
        jobs = {"shelters": do_shelters, "bond": do_bond, "dialysis": do_dialysis, "crossings": do_crossings}
        only = set(a.only.split(",")) if a.only else set(jobs)
        for k, fn in jobs.items():
            if k not in only:
                continue
            t0 = time.time()
            try:
                rep, n = fn(not a.dry_run)
                report[k] = {**rep, "count": n, "secs": round(time.time() - t0, 1)}
                if not a.dry_run:
                    snaps[k] = {"date": today, "count": n, "source": SOURCES[k]}
            except Exception as e:
                report[k] = {"error": f"{type(e).__name__}: {e}"}
    print(("DRY RUN - " if a.dry_run else "") + "Snapshot change report")
    for k, r in report.items():
        if "error" in r:
            print(f"  {k:10s} ERROR {r['error']} (kept current data)")
        else:
            print(f"  {k:10s} count={r['count']} added={r.get('added')} removed={r.get('removed')} changed={r.get('changed')}"
                  + (f"  [{r['note']}]" if r.get("note") else ""))
            for kind, ex in (r.get("examples") or {}).items():
                if ex:
                    print(f"             {kind}: {ex}")
    if not a.dry_run:
        man["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        SNAP.mkdir(parents=True, exist_ok=True)
        man_path.write_text(json.dumps(man, indent=1))
        print("wrote", man_path)


if __name__ == "__main__":
    main()
