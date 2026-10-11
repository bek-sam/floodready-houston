#!/usr/bin/env python3
"""Fetch NWS NWPS flood impact statements + Harvey crest per gauge into data/gauge_impacts.json."""
import json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.water.noaa.gov/nwps/v1/gauges/"

def fetch(lid):
    out = subprocess.run(["curl", "-sS", "--fail", "-m", "30", "-A", "FloodReadyHouston/0.1 (hackathon)", API + lid],
                         check=True, capture_output=True).stdout
    return json.loads(out).get("flood") or {}

result = {}
for g in json.loads((ROOT / "data" / "gauges.json").read_text()):
    lid = g["id"]
    try:
        flood = fetch(lid)
    except Exception as e:  # tolerate per-gauge failure
        print("FAIL", lid, e)
        continue
    impacts = sorted(({"stage": i["stage"], "statement": i["statement"]}
                      for i in flood.get("impacts") or [] if i.get("stage") is not None and i.get("statement")),
                     key=lambda i: i["stage"])
    harvey = None
    for c in (flood.get("crests") or {}).get("historic") or []:
        t = (c.get("occurredTime") or "")[:10]
        if "2017-08-25" <= t <= "2017-09-05" and c.get("stage") is not None:
            if harvey is None or c["stage"] > harvey["stage"]:
                harvey = {"stage": c["stage"], "occurred": t}
    result[lid] = {"impacts": impacts, "harvey_crest": harvey, "source": f"https://water.noaa.gov/gauges/{lid}"}
(ROOT / "data" / "gauge_impacts.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
print(len(result), "gauges ->", "data/gauge_impacts.json")
