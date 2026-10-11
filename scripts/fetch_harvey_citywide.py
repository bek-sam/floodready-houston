#!/usr/bin/env python3
"""Fetch the whole City of Houston Harvey inundation layer into data/harvey/harvey.sqlite.

Source: StormDrainage_Study MapServer layer 4 (maxRecordCount 2000, ~350k polygons).
Pages by OBJECTID ranges, <=3 concurrent workers, retries with backoff, resumable
(completed ranges are checkpointed in table `pages`). Geometry is simplified server-side
(maxAllowableOffset ~0.00005 deg) and stored as zlib-compressed JSON rings (6 dp) plus an
R*Tree bbox index. Usage: python scripts/fetch_harvey_citywide.py [--db PATH] [--workers 3]
"""
import argparse, subprocess, json, sqlite3, sys, time, zlib, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4"
PAGE = 2000
OFFSET = 0.00005
UA = {"User-Agent": "FloodReadyHouston/0.1 (hackathon)"}
DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "harvey" / "harvey.sqlite"


def get(url, params, tries=8):
    q = urllib.parse.urlencode(params)
    for a in range(tries):
        try:
            # curl uses the OS trust store (the City server sends an incomplete cert chain,
            # which Python's bundled CAs reject) -- verification stays on.
            out = subprocess.run(["curl", "-sS", "--fail", "-m", "120", "-A", UA["User-Agent"], f"{url}?{q}"],
                                 capture_output=True, check=True).stdout
            d = json.loads(out)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception as e:
            wait = min(60, 2 ** a)
            print(f"  retry {a+1}/{tries} after {e!r}; sleep {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError("giving up on " + q[:120])


def fetch_page(lo, hi):
    d = get(BASE + "/query", {
        "where": f"OBJECTID>={lo} AND OBJECTID<{hi}", "outFields": "OBJECTID,GRIDCODE",
        "outSR": 4326, "maxAllowableOffset": OFFSET, "geometryPrecision": 6, "f": "geojson"})
    return d.get("features", [])


def rings_of(geom):
    t, c = geom.get("type"), geom.get("coordinates")
    if t == "Polygon":
        return [c]
    if t == "MultiPolygon":
        return c
    return []


def init(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS polys(id INTEGER PRIMARY KEY, oid INTEGER, gridcode INTEGER, geom BLOB, nverts INTEGER);
    CREATE VIRTUAL TABLE IF NOT EXISTS poly_idx USING rtree(id, minx, maxx, miny, maxy);
    CREATE TABLE IF NOT EXISTS pages(lo INTEGER PRIMARY KEY, hi INTEGER, n_feat INTEGER);
    CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
    """)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    workers = max(1, min(3, a.workers))
    Path(a.db).parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    con = sqlite3.connect(a.db)
    init(con)
    info = get(BASE, {"f": "json"})
    print("maxRecordCount", info.get("maxRecordCount"), flush=True)
    ids = get(BASE + "/query", {"where": "1=1", "returnIdsOnly": "true", "f": "json"})["objectIds"]
    total, mn, mx = len(ids), min(ids), max(ids)
    print(f"layer: {total} objects, OID {mn}..{mx}", flush=True)
    done = {r[0] for r in con.execute("SELECT lo FROM pages")}
    ranges = [(lo, lo + PAGE) for lo in range(mn, mx + 1, PAGE) if lo not in done]
    print(f"{len(done)} pages done, {len(ranges)} to go", flush=True)
    n = 0
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fetch_page, lo, hi): (lo, hi) for lo, hi in ranges}
        for f in as_completed(futs):
            lo, hi = futs[f]
            feats = f.result()
            for ft in feats:
                p = ft.get("properties") or {}
                for poly in rings_of(ft.get("geometry") or {}):
                    if not poly or not poly[0]:
                        continue
                    xs = [pt[0] for r in poly[:1] for pt in r]
                    ys = [pt[1] for r in poly[:1] for pt in r]
                    nv = sum(len(r) for r in poly)
                    cur = con.execute("INSERT INTO polys(oid,gridcode,geom,nverts) VALUES(?,?,?,?)",
                                      (p.get("OBJECTID"), p.get("GRIDCODE"),
                                       zlib.compress(json.dumps(poly, separators=(",", ":")).encode()), nv))
                    con.execute("INSERT INTO poly_idx VALUES(?,?,?,?,?)",
                                (cur.lastrowid, min(xs), max(xs), min(ys), max(ys)))
            con.execute("INSERT OR REPLACE INTO pages VALUES(?,?,?)", (lo, hi, len(feats)))
            con.commit()
            n += 1
            print(f"page {lo}-{hi} feats={len(feats)} ({n}/{len(ranges)}) {time.time()-t0:.0f}s", flush=True)
    npoly = con.execute("SELECT count(*) FROM polys").fetchone()[0]
    nfeat = con.execute("SELECT count(DISTINCT oid) FROM polys").fetchone()[0]
    b = con.execute("SELECT min(minx),min(miny),max(maxx),max(maxy) FROM poly_idx").fetchone()
    meta = {"source": BASE, "layer_objects": total, "features_stored": nfeat, "polygons_stored": npoly,
            "coverage_bbox": list(b), "maxAllowableOffset": OFFSET, "complete": nfeat >= total,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for k, v in meta.items():
        con.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, json.dumps(v)))
    con.commit()
    if "--no-vacuum" not in sys.argv:
        con.execute("VACUUM")
    con.close()
    Path(a.db).with_name("coverage.json").write_text(json.dumps(meta, indent=2))
    print("DONE", meta, f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
