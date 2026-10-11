"""Expand data/crossings.geojson beyond the KPRC list. Idempotent: rebuilds extras from sources every run
(features whose properties.origin == 'extra' are dropped first). Run: cd backend && uv run python ../scripts/fetch_crossings_extra.py

Sources (all free): USGS STN Harvey high-water marks (Harris Co.), OpenStreetMap road tunnels/underpasses
(Overpass) kept only if inside the City of Houston Harvey inundation layer, and a Nominatim/Overpass retry of
KPRC entries the Census geocoder could not place.
RISK RULE: high = underpass/depressed road listed by City of Houston, OR OSM underpass inside Harvey extent,
OR a Harvey high-water mark >= 2 ft above ground at a named bridge/underpass/low-water crossing.
medium = flood-signal/barricade sites, and other Harvey HWMs at road bridges/crossings. Dedupe radius 60 m."""
import httpx, json, math, pathlib, re, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "crossings.geojson"
KPRC = "https://www.click2houston.com/news/local/2026/06/15/list-houston-area-intersections-roads-most-likely-to-flood-during-heavy-rain/"
STN = "https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=180&States=TX&County=Harris%20County"
OSM = "https://www.openstreetmap.org/"
HARVEY = "https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4"
H = httpx.Client(timeout=120, headers={"User-Agent": "FloodReadyHouston/0.1 (hackathon; contact bekbolsun446@gmail.com)"})
inbox = lambda la, lo: 29.5 < la < 30.2 and -95.9 < lo < -94.9

def dist(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(la))

d = json.load(open(OUT))
feats = [f for f in d["features"] if f["properties"].get("origin") != "extra"]
for f in feats: f["properties"].setdefault("origin", "kprc")
counts = {}

def add(name, lat, lon, risk, reasons, sources, tag):
    if not inbox(lat, lon): return
    for f in feats:
        c = f["geometry"]["coordinates"]
        if dist((lat, lon), (c[1], c[0])) <= 60:
            p = f["properties"]
            for s in sources:
                if s not in p["sources"]: p["sources"].append(s)
            for r in reasons:
                if r not in p["reasons"]: p["reasons"].append(r)
            if risk == "high": p["risk"] = "high"
            return
    feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                  "properties": {"id": "", "name": name, "risk": risk, "reasons": reasons, "sources": sources, "origin": "extra"}})
    counts[tag] = counts.get(tag, 0) + 1

def nominatim(q, street_words):
    time.sleep(1.1)
    try:
        r = H.get("https://nominatim.openstreetmap.org/search", params={"q": q, "format": "json", "limit": 1, "countrycodes": "us", "viewbox": "-95.9,30.2,-94.9,29.5", "bounded": 1}).json()
    except Exception as e:
        print("nominatim", q, e); return None
    if r:
        dn = r[0]["display_name"].lower()
        if all(w.lower() in dn for w in street_words) and inbox(float(r[0]["lat"]), float(r[0]["lon"])):
            return float(r[0]["lat"]), float(r[0]["lon"])

# 1. KPRC entries the Census geocoder missed
kp = pathlib.Path("/private/tmp/claude-501/kprc.txt")
if kp.exists():
    txt = kp.read_text()
    def block(a, b):
        i = txt.index(a); j = txt.index(b, i)
        return [l.strip() for l in txt[i:j].split("\n")[1:] if l.strip() and not l.startswith(("KPRC", "Recommended"))]
    have = {f["properties"]["name"] for f in feats}
    AMBIG = ("7000 Main", "7200 Senate")
    under = [l for l in block("City officials said the underpasses", "Flood signal locations") if re.match(r"\d", l)]
    sig = [l for l in block("City officials said to look for flood signals", "Houston flood trouble spots") if re.match(r"\d", l) or " & " in l]
    bar = [l for l in block("City officials said the following intersections", "Underpass locations") if " at " in l]
    R_U = ["Listed by City of Houston officials (via KPRC, June 2026) as an underpass that could become problematic in heavy rain",
           "Drivers drown in flooded underpasses; 3 drivers died at one Houston underpass in April 2016"]
    for l in under:
        if f"Underpass at {l}" in have or l.startswith(AMBIG): continue
        m = re.match(r"(\d+) (.+?)( Fr)?$", l)
        pt = nominatim(f"{m[1]} {m[2]}, Houston, Texas", [m[2].split()[0]]) if m else None
        if pt: add(f"Underpass at {l}", *pt, "high", R_U, [KPRC], "kprc_retry")
    for l in sig:
        if f"Flood signal site: {l}" in have: continue
        n = re.sub(r"\s*\(.*\)", "", l)
        if " & " in n:
            a, b = [x.strip() for x in n.split(" & ", 1)]
            pt = nominatim(f"{a} and {b}, Houston, Texas", [re.sub(r"(?i)\W|blvd|st$", "", a.split()[0])])
        else:
            m = re.match(r"(\d+) (.+)", n)
            pt = nominatim(f"{m[1]} {m[2]}, Houston, Texas", [m[2].split()[0]]) if m else None
        if pt: add(f"Flood signal site: {l}", *pt, "medium", ["City of Houston flood signal location (via KPRC, June 2026): watch for flashing flood signals in heavy rain"], [KPRC], "kprc_retry")
    for l in bar:
        if l in have: continue
        a, b = [x.strip() for x in l.split(" at ", 1)]
        b = re.sub(r"(?i)^(n|s|e|w|north|south|east|west)\.? ?of\.? ", "", b)
        if re.search(r"(?i)fwy|hwy|braes", b): continue  # freeway ramps cannot be pinned to one point reliably
        pt = nominatim(f"{a} and {b}, Houston, Texas", [a.split()[0].rstrip(".")])
        if pt: add(l, *pt, "medium", ["City officials say this intersection or underpass may be barricaded if flooding becomes a problem (via KPRC, June 2026)"], [KPRC], "kprc_retry")

# 2. USGS STN Harvey high-water marks at road crossings
hw = H.get(STN, timeout=180).json()
rx = re.compile(r"(?i)underpass|low.?water|crossing|bridge|culvert|under (?:the )?(?:fwy|freeway|hwy|rd|road|st|street)")
sites = {}
for x in hw:
    s = x.get("siteDescription") or ""
    if not rx.search(s) or x.get("latitude_dd") is None: continue
    k = x["site_id"]
    h = x.get("height_above_gnd") or 0
    if k not in sites or h > sites[k][0]: sites[k] = (h, s.strip(), x["latitude_dd"], x["longitude_dd"], x.get("waterbody"), x["hwm_id"])
for h, s, la, lo, wb, hid in sites.values():
    deep = h >= 2
    add(f"Harvey high-water mark: {s}", la, lo, "high" if deep else "medium",
        [f"USGS surveyed a Hurricane Harvey (2017) high-water mark at this road crossing{f', {h:g} ft above ground' if h else ''}" + (f" ({wb})" if wb else ""),
         "Low crossings and bridge approaches flood first; vehicles float in about 12 inches of moving water"],
        [f"https://stn.wim.usgs.gov/STNpublic/#/Data/HWM/{hid}", "https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=180"], "usgs_stn")

# 3. OSM road underpasses inside the City of Houston Harvey inundation layer
q = '[out:json][timeout:180];way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|motorway_link|trunk_link|primary_link|secondary_link)$"]["tunnel"~"^(yes|building_passage)$"](29.5,-95.9,30.2,-94.9);out center tags;'
els = []
for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
    try:
        r = H.post(url, data={"data": q}, timeout=200)
        if r.status_code == 200: els = r.json()["elements"]; break
    except Exception as e: print("overpass", e)
def in_harvey(lat, lon):
    try:
        j = H.get(HARVEY + "/query", params={"f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "returnCountOnly": "true"}).json()
        return j.get("count", 0) > 0
    except Exception: return False
for e in els:
    t = e["tags"]; la, lo = e["center"]["lat"], e["center"]["lon"]
    if t.get("access") in ("private", "no"): continue
    if not in_harvey(la, lo): continue
    nm = t.get("name") or t.get("ref") or "unnamed road"
    add(f"Underpass: {nm}", la, lo, "high",
        ["OpenStreetMap road underpass/tunnel inside the City of Houston Harvey (2017) inundation extent",
         "Drivers drown in flooded underpasses; 3 drivers died at one Houston underpass in April 2016"],
        [f"{OSM}way/{e['id']}", HARVEY], "osm_underpass")

# retried geocodes that landed far from the named street after manual sanity check, plus non-street tunnels
BAD = {"Underpass at 11700 West Park", "Underpass at 1900 Kelly", "Underpass at 3500 Kelly", "Underpass at 8000 Memorial",
       "Flood signal site: 7506 E Hardy Rd (Hardy Toll Road And Crosstimbers)", "Underpass: Washburn Tunnel", "Underpass: unnamed road"}
feats = [f for f in feats if f["properties"]["name"] not in BAD]
feats.sort(key=lambda f: (f["properties"]["origin"] != "kprc", f["properties"]["id"] or "z"))
for i, f in enumerate(feats): f["properties"]["id"] = f"x{i+1:03d}"
json.dump({"type": "FeatureCollection", "features": feats}, open(OUT, "w"), indent=1)
print("added", counts, "total", len(feats), "high", sum(f["properties"]["risk"] == "high" for f in feats))
