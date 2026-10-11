import httpx, json, concurrent.futures as cf
B="https://api.water.noaa.gov/nwps/v1/gauges"
c=httpx.Client(timeout=30,headers={"User-Agent":"FloodReadyHouston/0.1 (hackathon)"})
r=c.get(B,params={"bbox.xmin":-95.9,"bbox.ymin":29.5,"bbox.xmax":-94.9,"bbox.ymax":30.2,"srid":"EPSG_4326"}).json()
items=r.get("gauges",r)
print(len(items))
def det(g):
    try: return c.get(f"{B}/{g['lid']}").json()
    except Exception as e: return None
out=[]
with cf.ThreadPoolExecutor(8) as ex:
    for g,d in zip(items,ex.map(det,items)):
        if not d: continue
        fs=(d.get("flood") or {}).get("categories") or {}
        st={k:(fs.get(k) or {}).get("stage") for k in("action","minor","moderate","major")}
        st={k:(v if isinstance(v,(int,float)) and v>-900 else None) for k,v in st.items()}
        out.append({"id":d["lid"],"usgs_id":d.get("usgsId") or None,"name":d.get("name"),"lat":d.get("latitude"),"lon":d.get("longitude"),"flood_stages":st})
json.dump(out,open("data/gauges.json","w"),indent=1)
print(len(out),sum(1 for o in out if o["usgs_id"]),sum(1 for o in out if o["flood_stages"]["minor"] is not None))
