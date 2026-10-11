"""Extract Harvey inundation polygons for demo bboxes from City of Houston layer (slow; paginated, simplified)."""
import httpx, json, time
URL="https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4/query"
BB={"Meyerland":(-95.48,29.67,-95.44,29.70),"UH / Third Ward":(-95.36,29.71,-95.33,29.73),"Downtown / Buffalo Bayou":(-95.39,29.75,-95.35,29.77),"Kashmere Gardens / Hunting Bayou":(-95.33,29.79,-95.29,29.82)}
c=httpx.Client(timeout=180);feats=[];done={};t0=time.time()
for name,b in BB.items():
    if time.time()-t0>1200: break
    off=0;ok=True;n=0
    while True:
        p={"f":"geojson","geometry":",".join(map(str,b)),"geometryType":"esriGeometryEnvelope","inSR":4326,"outSR":4326,"spatialRel":"esriSpatialRelIntersects","outFields":"","returnGeometry":"true","maxAllowableOffset":0.0001,"resultOffset":off,"resultRecordCount":500,"geometryPrecision":5}
        j=None
        for _ in range(3):
            try: j=c.get(URL,params=p).json();break
            except Exception as e: print(name,e)
        if not j or "features" not in j: ok=False;break
        f=j["features"];feats+=f;n+=len(f);off+=len(f)
        if not f or not j.get("exceededTransferLimit") and len(f)<500: break
    print(name,n,ok)
    if ok: done[name]=list(b)
for f in feats: f["properties"]={}
json.dump({"type":"FeatureCollection","source":"https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4","coverage_bboxes":done,"note":"City of Houston Harvey inundation estimate (to 8/31/2017, riverine only), clipped by intersection to demo bboxes (whole polygons kept), simplified ~0.0001 deg. Not an official flood determination.","features":feats},open("data/harvey_inundation.geojson","w"),separators=(",",":"))
print(len(feats))

# --- shrink pass: round to 4 decimals, drop duplicate vertices and tiny features, to stay ~<5MB
def shrink(path="data/harvey_inundation.geojson",minspan=0.0003):
    d=json.load(open(path));out=[]
    def ring(r):
        q=[];[q.append([round(x,4),round(y,4)]) for x,y in r if not q or q[-1]!=[round(x,4),round(y,4)]]
        return q if len(q)>=4 else None
    for f in d["features"]:
        g=f["geometry"]
        if not g: continue
        polys=g["coordinates"] if g["type"]=="MultiPolygon" else [g["coordinates"]]
        keep=[]
        for pl in polys:
            ext=ring(pl[0])
            if not ext: continue
            xs=[p[0] for p in ext];ys=[p[1] for p in ext]
            if max(xs)-min(xs)<minspan and max(ys)-min(ys)<minspan: continue
            keep.append([ext]+[r for r in map(ring,pl[1:]) if r])
        if keep: out.append({"type":"Feature","properties":{},"geometry":{"type":"MultiPolygon","coordinates":keep}})
    d["features"]=out;json.dump(d,open(path,"w"),separators=(",",":"));print("shrunk",len(out))
if __name__=="__main__": shrink()
