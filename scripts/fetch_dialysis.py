"""Snapshot Harris County, TX dialysis facilities from CMS Provider Data -> data/dialysis.json."""
import json, pathlib, httpx

SRC = "https://data.cms.gov/provider-data/dataset/23ew-n7w9"
API = "https://data.cms.gov/provider-data/api/1/datastore/query/23ew-n7w9/0"
GEO = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

rows, off = [], 0
while True:
    r = httpx.get(API, params={"limit": 500, "offset": off, "conditions[0][property]": "state",
                  "conditions[0][value]": "TX", "conditions[1][property]": "countyparish",
                  "conditions[1][value]": "Harris"}, timeout=60).json()["results"]
    rows += r
    if len(r) < 500: break
    off += 500

out, skipped = [], 0
for x in rows:
    addr = f'{x["address_line_1"]}, {x["citytown"]}, TX {x["zip_code"][:5]}'
    try:
        m = httpx.get(GEO, params={"address": addr, "benchmark": "Public_AR_Current", "format": "json"},
                      timeout=30).json()["result"]["addressMatches"]
    except Exception:
        m = []
    if not m: skipped += 1; continue
    out.append({"name": x["facility_name"].title(), "address": x["address_line_1"].title(),
                "city": x["citytown"].title(), "zip": x["zip_code"][:5], "phone": x["telephone_number"],
                "lat": m[0]["coordinates"]["y"], "lon": m[0]["coordinates"]["x"]})
D = pathlib.Path(__file__).resolve().parent.parent / "data"
json.dump(out, open(D / "dialysis.json", "w"), indent=1)
(D / "dialysis.source.txt").write_text(f"{SRC}\ncount={len(out)}\n")
print(len(rows), "fetched,", len(out), "geocoded,", skipped, "skipped")
