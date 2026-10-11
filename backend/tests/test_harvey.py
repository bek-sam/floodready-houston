import json
import sqlite3
import zlib

import pytest
from fastapi.testclient import TestClient

from app.services import harvey


def _make_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE polys(id INTEGER PRIMARY KEY, oid INTEGER, gridcode INTEGER, geom BLOB, nverts INTEGER);
    CREATE VIRTUAL TABLE poly_idx USING rtree(id, minx, maxx, miny, maxy);
    CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
    """)
    # square (-95.5..-95.4, 29.6..29.7) with a hole (-95.47..-95.43, 29.64..29.66)
    outer = [[-95.5, 29.6], [-95.4, 29.6], [-95.4, 29.7], [-95.5, 29.7], [-95.5, 29.6]]
    hole = [[-95.47, 29.64], [-95.47, 29.66], [-95.43, 29.66], [-95.43, 29.64], [-95.47, 29.64]]
    poly = [outer, hole]
    cur = con.execute("INSERT INTO polys(oid,gridcode,geom,nverts) VALUES(1,1,?,10)",
                      (zlib.compress(json.dumps(poly).encode()),))
    con.execute("INSERT INTO poly_idx VALUES(?,?,?,?,?)", (cur.lastrowid, -95.5, -95.4, 29.6, 29.7))
    con.execute("INSERT INTO meta VALUES('coverage_bbox', ?)", (json.dumps([-95.6, 29.5, -95.3, 29.8]),))
    con.commit()
    con.close()


@pytest.fixture()
def fixture_db(tmp_path, monkeypatch):
    (tmp_path / "harvey").mkdir()
    _make_db(tmp_path / "harvey" / "harvey.sqlite")
    monkeypatch.setattr(harvey, "DATA_DIR", tmp_path)
    harvey._cov.update(key=None, bbox=None)
    return tmp_path


def test_point_in_polygon(fixture_db):
    assert harvey.harvey_at(29.62, -95.45)["flooded"] is True
    assert harvey.harvey_at(29.65, -95.45)["flooded"] is False   # in the hole
    assert harvey.harvey_at(29.75, -95.55)["flooded"] is False   # in coverage, outside polygons
    r = harvey.harvey_at(30.5, -95.45)                            # outside coverage
    assert r["flooded"] is None and "coverage" in r["note"]
    assert "not proof" in harvey.harvey_at(29.62, -95.45)["note"]


def test_missing_db_falls_back_to_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(harvey, "DATA_DIR", tmp_path)
    harvey._idx.update(loaded=False, polys=[], bbox=None, mtime=None)
    assert harvey.harvey_at(29.7, -95.4)["flooded"] is None


def test_extent_endpoint(fixture_db):
    from app.main import app
    c = TestClient(app)
    r = c.get("/api/harvey/extent", params={"bbox": "-95.6,29.5,-95.3,29.8", "limit": 10})
    assert r.status_code == 200
    d = r.json()
    assert d["type"] == "FeatureCollection" and len(d["features"]) == 1
    assert d["features"][0]["properties"]["source"]
    assert len(r.content) < 1_500_000
    empty = c.get("/api/harvey/extent", params={"bbox": "-90,29,-89,30"}).json()
    assert empty["features"] == []
    assert c.get("/api/harvey/extent", params={"bbox": "bad"}).status_code == 422


def test_extent_vertex_cap(fixture_db):
    big = [[-95.5 + i * 1e-6, 29.6 + (i % 2) * 0.01] for i in range(5000)]
    big.append(big[0])
    out = harvey._thin(big, 100)
    assert len(out) <= 101


def test_extent_clips_to_bbox(fixture_db):
    bb = [-95.49, 29.61, -95.48, 29.62]   # tiny window inside the big square
    d = harvey.extent_geojson(bb)
    assert len(d["features"]) == 1
    for f in d["features"]:
        for ring in f["geometry"]["coordinates"]:
            for x, y in ring:
                assert bb[0] - 1e-9 <= x <= bb[2] + 1e-9 and bb[1] - 1e-9 <= y <= bb[3] + 1e-9
    # window overlapping only the hole -> nothing
    assert harvey.extent_geojson([-95.46, 29.645, -95.44, 29.655])["features"] == []
