#!/usr/bin/env python3
"""Snapshot USGS STN Harvey (event 180) Texas high-water marks into data/hwm_harvey.json."""
import json, subprocess, datetime
from pathlib import Path

URL = "https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=180&States=TX"
OUT = Path(__file__).resolve().parents[1] / "data" / "hwm_harvey.json"

# curl uses the OS trust store (python's bundled certs fail on some macOS installs)
rows = json.loads(subprocess.run(["curl", "-sS", "--fail", "-m", "120", "-A", "FloodReadyHouston/0.1", URL],
                                 check=True, capture_output=True).stdout)
marks = []
for r in rows:
    if r.get("height_above_gnd") is None or r.get("latitude_dd") is None:
        continue
    marks.append({"id": r["hwm_id"], "lat": r["latitude_dd"], "lon": r["longitude_dd"],
                  "h": r["height_above_gnd"], "elev": r.get("elev_ft"),
                  "q": r.get("hwmQualityName"), "county": r.get("countyName"),
                  "desc": r.get("siteDescription"), "date": (r.get("survey_date") or "")[:10]})
OUT.write_text(json.dumps({"event": "Harvey 2017", "source": "USGS STN event 180", "url": URL,
                           "snapshot_date": datetime.date.today().isoformat(), "marks": marks},
                          separators=(",", ":")))
print(len(rows), "rows;", len(marks), "marks with height above ground ->", OUT)
