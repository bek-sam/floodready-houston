"""Harvey inundation lookup from data/harvey_inundation.geojson (point-in-polygon, bbox prefilter)."""
import json
import sqlite3
import zlib

from app.config import DATA_DIR

SOURCE = "https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4"
NO_DATA = {"flooded": None, "source": SOURCE, "note": "No Harvey extent data for this location", "note_code": "harvey.nodata"}
_idx = {"loaded": False, "polys": [], "bbox": None, "mtime": None}


def _rings(geom):
    t, c = geom.get("type"), geom.get("coordinates")
    if t == "Polygon":
        return [c]
    if t == "MultiPolygon":
        return c
    return []


def _load():
    p = DATA_DIR / "harvey_inundation.geojson"
    try:
        m = p.stat().st_mtime
    except OSError:
        _idx.update(loaded=True, polys=[], bbox=None, mtime=None)
        return
    if _idx["loaded"] and _idx["mtime"] == m:
        return
    polys, bb = [], [180, 90, -180, -90]
    try:
        for f in json.loads(p.read_text()).get("features", []):
            for poly in _rings(f.get("geometry") or {}):
                xs = [pt[0] for pt in poly[0]]
                ys = [pt[1] for pt in poly[0]]
                b = (min(xs), min(ys), max(xs), max(ys))
                polys.append((b, poly))
                bb = [min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3])]
    except Exception:
        polys = []
    _idx.update(loaded=True, polys=polys, bbox=bb if polys else None, mtime=m)


def _in_ring(x, y, ring) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def harvey_at_legacy(lat: float, lon: float) -> dict:
    _load()
    bb = _idx["bbox"]
    if not bb or not (bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3]):
        return dict(NO_DATA)
    for b, poly in _idx["polys"]:
        if b[0] <= lon <= b[2] and b[1] <= lat <= b[3] and _in_ring(lon, lat, poly[0]) \
                and not any(_in_ring(lon, lat, h) for h in poly[1:]):
            return {"flooded": True, "source": SOURCE,
                    "note": "This location is inside the City of Houston's estimated Harvey inundation extent (riverine only).",
                    "note_code": "harvey.hit"}
    return {"flooded": False, "source": SOURCE,
            "note": ("Not inside our simplified copy of the City's estimated Harvey riverine extent — this is not proof it stayed dry. "
                    "About half of Harvey-flooded homes were outside mapped floodplains, and street flooding isn't in this map."),
            "note_code": "harvey.miss"}


# ---- citywide SQLite + R*Tree index (scripts/fetch_harvey_citywide.py) ----
CITY_SOURCE = SOURCE
HIT_NOTE = ("This location is inside the City of Houston's estimated Harvey inundation extent "
            "(a riverine model estimate to 8/31/2017, not proof of flooding at this address).")
MISS_NOTE = ("Not inside the City of Houston's estimated Harvey riverine extent (simplified copy). This is not proof it stayed dry: "
             "about half of Harvey-flooded homes were outside mapped floodplains, and street/drainage flooding isn't in this map.")
OUT_NOTE = "Outside the City of Houston Harvey layer's coverage, so we have no Harvey extent data for this location."


def _db_path():
    return DATA_DIR / "harvey" / "harvey.sqlite"


def _connect():
    p = _db_path()
    if not p.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        con.execute("SELECT 1 FROM poly_idx LIMIT 1")
        return con
    except sqlite3.Error:
        return None


_cov = {"key": None, "bbox": None}


def coverage(con) -> list | None:
    key = (str(_db_path()), _db_path().stat().st_mtime)
    if _cov["key"] != key:
        try:
            r = con.execute("SELECT v FROM meta WHERE k='coverage_bbox'").fetchone()
            bb = json.loads(r[0]) if r else None
        except sqlite3.Error:
            bb = None
        if not bb:
            r = con.execute("SELECT min(minx),min(miny),max(maxx),max(maxy) FROM poly_idx").fetchone()
            bb = list(r) if r and r[0] is not None else None
        _cov.update(key=key, bbox=bb)
    return _cov["bbox"]


def _inside(x, y, poly) -> bool:
    return _in_ring(x, y, poly[0]) and not any(_in_ring(x, y, h) for h in poly[1:])


def harvey_at(lat: float, lon: float) -> dict:
    """flooded True/False/None for a point. Citywide index first, then the old 4-area file."""
    con = _connect()
    if con is None:
        return harvey_at_legacy(lat, lon)
    try:
        bb = coverage(con)
        if not bb or not (bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3]):
            return {"flooded": None, "source": CITY_SOURCE, "note": OUT_NOTE, "note_code": "harvey.out"}
        rows = con.execute(
            "SELECT p.geom FROM poly_idx i JOIN polys p ON p.id=i.id "
            "WHERE i.minx<=? AND i.maxx>=? AND i.miny<=? AND i.maxy>=?", (lon, lon, lat, lat))
        for (blob,) in rows:
            if _inside(lon, lat, json.loads(zlib.decompress(blob))):
                return {"flooded": True, "source": CITY_SOURCE, "note": HIT_NOTE, "note_code": "harvey.hit"}
        return {"flooded": False, "source": CITY_SOURCE, "note": MISS_NOTE, "note_code": "harvey.miss"}
    except sqlite3.Error:
        return harvey_at_legacy(lat, lon)
    finally:
        con.close()


def _thin(ring, budget):
    if len(ring) <= budget:
        return [[round(x, 5), round(y, 5)] for x, y in ((p[0], p[1]) for p in ring)]
    step = len(ring) / budget
    out = [ring[int(i * step)] for i in range(budget)]
    out.append(out[0])
    return [[round(p[0], 5), round(p[1], 5)] for p in out]


def extent_geojson(bbox, limit: int = 1500, max_vertices: int = 30000) -> dict:
    """Simplified GeoJSON of inundation polygons intersecting bbox (minx,miny,maxx,maxy).
    Capped by feature count and total vertices so the response stays well under 1.5 MB."""
    limit = max(1, min(int(limit), 5000))
    base = {"type": "FeatureCollection", "features": [], "properties": {
        "source": CITY_SOURCE, "truncated": False,
        "note": "City of Houston estimated Harvey riverine inundation, simplified. An estimate, not proof for any address."}}
    con = _connect()
    if con is None:
        # legacy fallback: old 4-area file
        _load()
        n = 0
        for b, poly in _idx["polys"]:
            if b[0] <= bbox[2] and b[2] >= bbox[0] and b[1] <= bbox[3] and b[3] >= bbox[1]:
                if n >= limit:
                    base["properties"]["truncated"] = True
                    break
                base["features"].append({"type": "Feature", "properties": {"source": SOURCE},
                                         "geometry": {"type": "Polygon", "coordinates": [_thin(r, 200) for r in poly]}})
                n += 1
        return base
    try:
        from shapely import make_valid
        from shapely.geometry import Polygon, box
        clip = box(*bbox)
        # largest polygons first so a truncated response still shows the main extent
        rows = con.execute(
            "SELECT p.geom FROM poly_idx i JOIN polys p ON p.id=i.id "
            "WHERE i.maxx>=? AND i.minx<=? AND i.maxy>=? AND i.miny<=? "
            "ORDER BY (i.maxx-i.minx)*(i.maxy-i.miny) DESC LIMIT ?",
            (bbox[0], bbox[2], bbox[1], bbox[3], limit * 2 + 1)).fetchall()
        if len(rows) > limit * 2:
            rows = rows[:limit * 2]
            base["properties"]["truncated"] = True
        clipped = []
        for (blob,) in rows:
            poly = json.loads(zlib.decompress(blob))
            try:
                g = Polygon(poly[0], poly[1:])
                if not g.is_valid:
                    g = make_valid(g)
                g = g.intersection(clip)
            except Exception:
                continue
            if not g.is_empty:
                clipped.append(g)
        tol = (bbox[2] - bbox[0]) / 1500
        for _ in range(8):
            simp = [x for x in (g.simplify(tol, preserve_topology=True) for g in clipped) if not x.is_empty]
            nv = sum(len(c) for g in simp for c in _polys_coords(g))
            if nv <= max_vertices:
                break
            tol *= 2
            base["properties"]["truncated"] = True
        used = 0
        for g in simp:
            for rings in _polys_coords(g):
                used += len(rings)
                if len(base["features"]) >= limit or used > max_vertices * 1.2:
                    base["properties"]["truncated"] = True
                    return base
                base["features"].append({"type": "Feature", "properties": {"source": CITY_SOURCE},
                                         "geometry": {"type": "Polygon", "coordinates": [
                                             [[round(x, 5), round(y, 5)] for x, y in r] for r in rings_of(rings)]}})
        return base
    finally:
        con.close()


def _polys_coords(g):
    """Yield one ring-list per Polygon in g (Polygon / Multi* / collection); ring-list items are Polygon objects."""
    t = g.geom_type
    if t == "Polygon":
        yield _PolyRings(g)
    elif hasattr(g, "geoms"):
        for sub in g.geoms:
            yield from _polys_coords(sub)


class _PolyRings(list):
    def __init__(self, g):
        super().__init__(g.exterior.coords)
        self.g = g


def rings_of(pr):
    return [list(pr.g.exterior.coords)] + [list(i.coords) for i in pr.g.interiors]
