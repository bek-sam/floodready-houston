import httpx, json
U="https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Evacuation_Shelters/FeatureServer/0/query"
r=httpx.get(U,params={"where":"1=1","outFields":"*","outSR":4326,"f":"geojson","resultRecordCount":2000},timeout=60).json()
assert r.get("features"),"no features"
json.dump(r,open(__import__("pathlib").Path(__file__).resolve().parent.parent/"data"/"shelters.json","w"))
print(len(r["features"]))
