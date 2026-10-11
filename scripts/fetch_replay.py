import httpx, json, datetime as dt
G={g["usgs_id"]:g for g in json.load(open("data/gauges.json")) if g["usgs_id"]}
EV=[("harvey-2017","Hurricane Harvey","2017-08-25","2017-09-02","Harvey flooded 154,170 Harris County homes; only 36% were insured, and nearly half were outside the 100- and 500-year floodplains. 36 Harris County deaths.","https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county"),
("taxday-2016","Tax Day Flood","2016-04-17","2016-04-20","12-16 inches of rain in 12 hours; about 9,820 structures flooded and 7 deaths in Harris County.","https://www.hcfcd.org/portals/62/about/flooding-history/historytimeline-24x36-1.pdf"),
("imelda-2019","Tropical Storm Imelda","2019-09-18","2019-09-21","About 8,200 homes flooded across 4 counties; 2 Harris County deaths and at least 1,700 rescues.","https://en.wikipedia.org/wiki/Tropical_Storm_Imelda_(2019)"),
("june-2026","June 2026 flash flood","2026-06-14","2026-06-17","Downtown flooding on June 15, 2026: cars stranded under bridges, UH-Downtown closed, state disaster declaration.","https://www.click2houston.com/news/local/2026/06/16/this-is-not-over-harris-county-braces-for-more-flooding/")]
c=httpx.Client(timeout=90)
def get(site,s,e):
    url="https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items"
    out=[];params={"f":"json","monitoring_location_id":"USGS-"+site,"parameter_code":"00065","time":f"{s}T00:00:00Z/{e}T23:59:59Z","limit":10000}
    for _ in range(10):
        try: r=c.get(url,params=params)
        except Exception as ex: print(site,ex); break
        if r.status_code!=200: print(site,r.status_code); break
        j=r.json()
        out+=[(f["properties"]["time"],float(f["properties"]["value"])) for f in j["features"] if f["properties"]["value"] not in (None,"")]
        nxt=[l["href"] for l in j.get("links",[]) if l.get("rel")=="next"]
        if not nxt: break
        r=None; url=nxt[0]; params=None
    return out
def hourly(pts):
    d={}
    for t,v in pts:
        x=dt.datetime.fromisoformat(t); u=x.astimezone(dt.timezone.utc).replace(minute=0,second=0,microsecond=0)
        d[u]=v  # last value in hour
    return [{"t":k.strftime("%Y-%m-%dT%H:%M:%SZ"),"stage_ft":round(v,2)} for k,v in sorted(d.items())]
evs=[]
for id,name,s,e,sm,src in EV:
    gs=[]
    for site,g in G.items():
        if site.startswith("0811"): continue
        ser=hourly(get(site,s,e))
        if len(ser)>=12:
            gs.append({"id":g["id"],"name":g["name"],"lat":g["lat"],"lon":g["lon"],"flood_stages":g["flood_stages"],"series":ser})
    ev={"id":id,"name":name,"start":s,"end":e,"summary":sm,"source":src}
    json.dump({"event":ev,"gauges":gs},open(f"data/replay/{id}.json","w"))
    evs.append(ev); print(id,len(gs),[ (g["id"],round(max(p["stage_ft"] for p in g["series"]),1)) for g in gs][:40])
json.dump(evs,open("data/replay/events.json","w"),indent=1)
