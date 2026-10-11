"""Build frontend/public/evidence.json from repo reports. Fails loudly on missing/unparsable sources.
Usage: python3 scripts/build_evidence.py [--skip-tests]   (tests: cd backend && uv run pytest -q)"""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "frontend" / "public" / "evidence.json"


def read(rel):
    p = ROOT / rel
    if not p.exists():
        sys.exit(f"MISSING source: {rel}")
    return p.read_text()


def grab(rx, text, rel):
    m = re.search(rx, text, re.S | re.M)
    if not m:
        sys.exit(f"UNPARSABLE {rel}: pattern {rx!r}")
    return m


def item(id, label, value, detail, as_of, path, url=None):
    return dict(id=id, label=label, value=value, detail=detail, as_of=as_of, source_path=path, source_url=url)


def eval_item(id, label, rel):
    t = read(rel)
    m = grab(r"Run: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}).*?Pass rate: (\d+)/(\d+) \((\d+)%\)", t, rel)
    ts, a, b, pct = m.groups()
    fails = re.findall(r"^### (\S+) \[", t, re.M)
    langs = {k: f"{p}/{n}" for k, p, n in re.findall(r"^\| lang: (\w+) \| (\d+) \| (\d+) \|", t, re.M)}
    detail = "by language: " + ", ".join(f"{k} {v}" for k, v in langs.items())
    detail += f"; known failures: {', '.join(fails)}" if fails else "; no failures"
    return item(id, label, f"{a}/{b} ({pct}%)", detail, ts, rel)


def main():
    items = [
        eval_item("ai_eval", "AI eval pass rate", "docs/eval/latest.md"),
        eval_item("citation_eval", "Citation eval (live Gemini)", "docs/eval/latest-citations.md"),
    ]
    # voice latency
    rel = "docs/eval/live-bench.md"
    t = read(rel)
    asof = grab(r"Run (\d{4}-\d{2}-\d{2} \d{2}:\d{2})", t, rel).group(1)
    n = int(grab(r"(\d+) sessions per model", t, rel).group(1))
    chosen = grab(r"Recommendation: `([^`]+)`", t, rel).group(1)
    row = grab(r"^\| " + re.escape(chosen) + r" \| (\d+)/(\d+) \| (\d+) \|", t, rel)
    ms = int(row.group(3))
    items.append(item("voice_latency", "Voice latency (end of speech to first audio)", f"median {ms/1000:.1f} s",
                      f"{chosen}, n={row.group(2)} (small sample); includes ~600 ms VAD silence wait", asof, rel))
    # tests
    if "--skip-tests" in sys.argv:
        sys.exit("tests required: refusing to emit a default number")
    r = subprocess.run(["uv", "run", "pytest", "-q"], cwd=ROOT / "backend", capture_output=True, text=True)
    last = [l for l in r.stdout.strip().splitlines() if l.strip()][-1] if r.stdout.strip() else ""
    m = re.search(r"(\d+) passed", last)
    if r.returncode != 0 or not m:
        sys.exit(f"pytest failed or unparsable: {last!r}")
    fl = re.search(r"(\d+) failed", last)
    items.append(item("tests", "Backend tests", f"{m.group(1)} passed", last.strip("= "),
                      datetime.now().strftime("%Y-%m-%d %H:%M"), "backend/tests"))
    # a11y
    rel = "docs/eval/a11y.md"
    t = read(rel)
    grab(r"axe-core 4\.10\.2", t, rel); grab(r"0 violations of any impact in all 48", t, rel)
    items.append(item("a11y", "Accessibility (axe-core 4.10.2)", "0 violations in 48 combos",
                      "12 views x 2 widths x 2 themes; was 1 serious + moderate before fixes; reported in CHANGELOG cycle 31, raw JSON not kept",
                      "2026-10-11", rel))
    # coverage
    rel = "docs/cycles/cycle-35-coverage.md"
    t = read(rel)
    grab(r"Recount: (\d+) REDUCES", t, rel)  # fail loudly if the doc has no recount line
    # the doc appends a new recount after each build; the last one is current
    a, b, c, tot = re.findall(r"Recount: (\d+) REDUCES / (\d+) INFORMS / (\d+) NONE of (\d+)", t)[-1]
    items.append(item("coverage", "Flood problems addressed", f"{a}/{tot} reduce, {b} inform, {c} not addressed",
                      "counted by hand per docs/cycles/cycle-24-coverage.md rules", "2026-10-11", rel))
    OUT.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": items}, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(items)} items)")


main()
