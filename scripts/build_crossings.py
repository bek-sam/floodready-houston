"""Build data/crossings.geojson from the KPRC June 2026 list (City of Houston/TranStar lists) via geocoding."""
import httpx, json, re, time, pathlib
SRC="https://www.click2houston.com/news/local/2026/06/15/list-houston-area-intersections-roads-most-likely-to-flood-during-heavy-rain/"
txt=pathlib.Path("/private/tmp/claude-501/kprc.txt").read_text() if pathlib.Path("/private/tmp/claude-501/kprc.txt").exists() else ""
def block(a,b):
    i=txt.index(a);j=txt.index(b,i);return [l.strip() for l in txt[i:j].split("\n")[1:] if l.strip() and not l.startswith(("KPRC","Recommended"))]
bar=block("City officials said the following intersections","Underpass locations")
bar=[l for l in bar if " at " in l]
under=block("City officials said the underpasses","Flood signal locations")
under=[l for l in under if re.match(r"\d",l)]
sig=block("City officials said to look for flood signals","Houston flood trouble spots")
sig=[l for l in sig if re.match(r"\d",l) or " & " in l]
H=httpx.Client(timeout=30,headers={"User-Agent":"FloodReadyHouston/0.1 (hackathon)"})
def inbox(la,lo): return 29.5<la<30.2 and -95.9<lo<-94.9
def census(addr):
    a=re.sub(r"\s*\(.*\)","",addr)
    a=re.sub(r"\bFr\b","",a)
    try:
        r=H.get("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress",params={"address":a+", Houston, TX","benchmark":"Public_AR_Current","format":"json"}).json()
        m=r["result"]["addressMatches"]
        if m:
            st=re.sub(r"^\d+\s+","",a).split()[0].lower()
            ma=m[0]["matchedAddress"].lower()
            if st not in ma: return None
            # require the matched ZIP to be a Houston-area ZIP (770xx-772xx)
            z=re.search(r"\b(77\d{3})\b",ma)
            if not z or not (77001<=int(z[1])<=77299): return None
            return m[0]["coordinates"]["y"],m[0]["coordinates"]["x"]
    except Exception as e: print("census",addr,e)
def street_q(n):
    n=n.strip().rstrip(".")
    if re.search(r"(?i)\bI-?10\b|katy fwy|katy freeway",n): return '["ref"~"I 10"]'
    if re.search(r"(?i)\b45\b",n) and re.search(r"(?i)fwy|freeway|ih-45",n): return '["ref"~"I 45"]'
    if re.search(r"(?i)\b59\b",n): return '["ref"~"US 59|I 69"]'
    if re.search(r"(?i)610",n): return '["ref"~"I 610"]'
    if re.search(r"(?i)U\.?S\.? 90",n): return '["ref"~"US 90"]'
    if re.search(r"(?i)hardy toll",n): return '["name"~"Hardy Toll"]'
    n=re.sub(r"(?i)^(\d+ )?(west|north|south|east|[nswe]\.?) ?of\.? ","",n)
    n=re.sub(r"(?i)\s+(road|rd|street|st|drive|dr|avenue|ave|boulevard|blvd|parkway|pkwy|trail|trl)\.?$","",n.strip())
    n=re.sub(r"^\d+ ","",n).replace(".","").strip()
    return '["name"~"^%s( |$)"]'%n
def nom(pair):
    a,b=pair
    q='[out:json][timeout:60];way["highway"]%s(29.5,-95.9,30.2,-94.9)->.a;way["highway"]%s(29.5,-95.9,30.2,-94.9)->.b;node(w.a)(w.b);out 3;'%(street_q(a),street_q(b))
    for _ in range(3):
        time.sleep(2)
        try:
            r=H.get("https://overpass-api.de/api/interpreter",params={"data":q})
            if r.status_code==200:
                el=r.json()["elements"]
                if el:
                    return sum(e["lat"] for e in el[:1]),el[0]["lon"]
                return None
            time.sleep(5)
        except Exception as e: print("ovp",pair,e)
def census2(addr):
    pt=census(addr)
    if pt: return pt
    m=re.match(r"(\d+) (.+)",addr)
    for suf in ("St","Rd","Dr","Blvd","Ave"):
        pt=census(f"{m[1]} {m[2]} {suf}")
        if pt and inbox(*pt): return pt
feats=[];skipped=[]
def add(name,pt,kind,reasons,risk):
    if not pt or not inbox(*pt): skipped.append(name);return
    feats.append({"type":"Feature","geometry":{"type":"Point","coordinates":[round(pt[1],6),round(pt[0],6)]},"properties":{"id":f"x{len(feats)+1:03d}","name":name,"risk":risk,"reasons":reasons,"sources":[SRC]}})
for l in under:
    add(f"Underpass at {l}",census2(l),"u",["Listed by City of Houston officials (via KPRC, June 2026) as an underpass that could become problematic in heavy rain","Drivers drown in flooded underpasses; 3 drivers died at one Houston underpass in April 2016"],"high")
for l in sig:
    n=re.sub(r"\s*\(.*\)","",l)
    pt=census2(n) if re.match(r"\d",n) and " & " not in n else (nom(tuple(x.strip() for x in n.split(" & ",1))) if " & " in n else None)
    add(f"Flood signal site: {l}",pt,"s",["City of Houston flood signal location (via KPRC, June 2026): watch for flashing flood signals in heavy rain"],"medium")
for l in bar:
    a,b=[x.strip() for x in l.split(" at ",1)]
    a=re.sub(r"^\d+ ","",a); b=re.sub(r"^(West|North|South|East|W\.|N\.|S\.|E\.) ?(of|Of)\.? ","",b)
    b=re.sub(r"^(S|N|W|E)\. ?(of|Of) ","",b)
    add(f"{l}",nom((a,b)) if "Braes Bayou" not in b else None,"b",["City officials say this intersection or underpass may be barricaded if flooding becomes a problem (via KPRC, June 2026)"],"medium")
# ambiguous geocodes removed after manual sanity check
BAD={"Underpass at 7000 Main","Underpass at 7200 Senate Ave"}
feats=[f for f in feats if f["properties"]["name"] not in BAD]
for i,f in enumerate(feats): f["properties"]["id"]=f"x{i+1:03d}"
json.dump({"type":"FeatureCollection","features":feats},open("data/crossings.geojson","w"),indent=1)
print(len(under),len(sig),len(bar),"-> features",len(feats),"skipped",len(skipped));print(skipped)
