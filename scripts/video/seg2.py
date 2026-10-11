import httpx, json, subprocess, sys, os
FF=sys.argv[1]
key=[l.split("=",1)[1].strip().strip('"') for l in open("../../.env") if l.startswith("ELEVENLABS_API_KEY=")][0]
V="nPczCjzI2devNBz1zQrb"
segs={
"p1":"Hurricane Harvey flooded 154,170 homes in Harris County.",
"p2":"Only 36 percent of them had flood insurance. And nearly half were outside the floodplain maps people trusted.",
"p3":"Worse, 77 percent of Texas flood deaths happen to people driving into water.",
"p4":"So we built FloodReady Houston. Your address, your route, your language. Know the real flood risk, before the water rises.",
}
segs.update({k:v for k,v in json.load(open("app_segs.json")).items()})
dur={}
for k,t in segs.items():
    r=httpx.post(f"https://api.elevenlabs.io/v1/text-to-speech/{V}",headers={"xi-api-key":key},json={"text":t,"model_id":"eleven_multilingual_v2","voice_settings":{"stability":0.45,"similarity_boost":0.8,"style":0.35,"use_speaker_boost":True}},timeout=90)
    r.raise_for_status(); open(f"{k}.mp3","wb").write(r.content)
    d=subprocess.run([FF,"-i",f"{k}.mp3"],capture_output=True,text=True).stderr.split("Duration: ")[1].split(",")[0]; h,m,s=d.split(":"); dur[k]=float(m)*60+float(s)
print(dur); json.dump(dur,open("dur.json","w"))
