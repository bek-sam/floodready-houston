"""Add `short_name` (<=60 chars) to every crossing in data/crossings.geojson. Keeps `name`. Idempotent."""
import json, re, pathlib

P = pathlib.Path(__file__).resolve().parent.parent / "data" / "crossings.geojson"
HWM = "Harvey high-water mark: "
SIG = "Flood signal site: "


def short(name: str) -> str:
    tag, n = "", name
    if n.startswith(HWM):
        n, tag = n[len(HWM):], " (Harvey HWM)"
    elif n.startswith(SIG):
        n = n[len(SIG):]
    n = re.sub(r"USACE Water-Surface measure point at\s*", "", n, flags=re.I)
    # split at the first sentence end, not at abbreviations like "N." "Rd." "St."
    n = re.split(r"(?<!\b[NSEW])(?<!\bRd)(?<!\bSt)(?<!\bDr)(?<!\bAve)(?<!\bBlvd)(?<!\bLn)(?<!\bHwy)\. ", n)[0].rstrip(". ")
    n = re.sub(r"\s*\([^)]*\)\s*$", "", n) if len(n) + len(tag) > 60 and "(" in n else n
    room = 60 - len(tag)
    if len(n) > room:
        n = n[: room - 1].rstrip(" ,") + "…"
    return n + tag


d = json.load(open(P))
for f in d["features"]:
    p = f["properties"]
    p["short_name"] = short(p["name"])
json.dump(d, open(P, "w"), ensure_ascii=False, indent=2)
print(len(d["features"]), "max", max(len(f["properties"]["short_name"]) for f in d["features"]))
