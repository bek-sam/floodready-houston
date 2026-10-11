import json, time, re
from playwright.sync_api import sync_playwright
dur=json.load(open("dur.json")); marks={}
B="http://localhost:5173"
def tr(f):
    try: f()
    except Exception as e: print("WARN",str(e)[:120])
with sync_playwright() as p:
    br=p.chromium.launch()
    ctx=br.new_context(viewport={"width":1280,"height":800},record_video_dir="vid",record_video_size={"width":1280,"height":800})
    pg=ctx.new_page(); t0=time.time()
    def mark(k): marks[k]=time.time()-t0
    def go_step(i):
        pg.goto(B+"/?demo=1#judge"); pg.wait_for_load_state("networkidle")
        tr(lambda: pg.locator("main button", has_text=re.compile("^(Go|Ir)")).nth(i).click(timeout=5000))
    def until(k, extra=0.6):
        end=marks[k]+dur[k]+extra
        while time.time()-t0<end: pg.wait_for_timeout(300)
    def at(k, frac): 
        while time.time()-t0 < marks[k]+dur[k]*frac: pg.wait_for_timeout(200)
    import os
    for k,h in zip(["p1","p2","p3","p4"],"abcd"):
        pg.goto("file://"+os.path.abspath("slides.html")+"?s="+h); pg.wait_for_timeout(500 if k!="p1" else 1200)
        mark(k); until(k,0.5)
    go_step(0); pg.wait_for_timeout(2500); pg.wait_for_load_state("networkidle")
    mark("s2")
    at("s2",0.2); tr(lambda: pg.get_by_text("Flood history here").click(timeout=3000))
    at("s2",0.4); tr(lambda: pg.get_by_text("Evacuation zone and storm surge").click(timeout=3000)); pg.mouse.move(400,500); pg.mouse.wheel(0,350)
    at("s2",0.6); tr(lambda: pg.get_by_text("Renting or buying here?").click(timeout=3000)); pg.mouse.wheel(0,350)
    at("s2",0.75); pg.mouse.wheel(0,-2000); pg.evaluate("window.scrollTo(0,0)"); tr(lambda: pg.locator("main").evaluate("e=>e.scrollTo&&e.scrollTo(0,0)"))
    until("s2")
    go_step(1); pg.wait_for_timeout(1500)
    tr(lambda: pg.get_by_role("button", name=re.compile("Check route")).first.click(timeout=4000))
    pg.wait_for_timeout(3000); mark("s3"); until("s3")
    tr(lambda: pg.get_by_role("link", name="After a flood").first.click(timeout=3000)); pg.wait_for_timeout(1800)
    mark("s6"); at("s6",0.5); pg.mouse.move(640,500); pg.mouse.wheel(0,500); until("s6")
    go_step(3); pg.wait_for_timeout(2000)
    tr(lambda: pg.get_by_role("textbox").last.press("Enter", timeout=3000))
    mark("s4")
    tr(lambda: pg.get_by_text(re.compile("911")).last.wait_for(timeout=12000))
    at("s4",0.5); pg.mouse.move(640,500); pg.mouse.wheel(0,400); until("s4")
    tr(lambda: pg.get_by_role("link", name=re.compile("Demo para jueces|Judge demo")).first.click(timeout=3000)); pg.wait_for_timeout(1500)
    mark("s5"); at("s5",0.3); pg.mouse.move(640,500); pg.mouse.wheel(0,600); at("s5",0.6); pg.mouse.wheel(0,600); until("s5",1.2)
    vp=pg.video.path(); ctx.close(); br.close()
json.dump({"marks":marks,"video":vp},open("marks.json","w")); print(marks)
