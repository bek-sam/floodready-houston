"""RAG: chunk markdown by heading, BM25 always, Gemini embeddings when available."""
import hashlib
import re

import numpy as np
from rank_bm25 import BM25Okapi

from .config import BACKEND, ROOT, database_url, sqlalchemy_url, embed_model, gemini_key

EMBED_DIM = 768
URL_RE = re.compile(r"https?://[^\s)\]>|,;]+")
HEAD_RE = re.compile(r"^(#{1,4})\s+(.*)")


def _tok(s: str) -> list[str]:
    return [re.sub(r"(ing|ed|es|s)$", "", w) if len(w) > 4 else w for w in re.findall(r"[a-z0-9]+", s.lower())]


KNOWLEDGE_BOOST = 0.15
EMOJI_RE = re.compile("[\u2705\U0001F7E1\u274C\U0001F7E2\u2B50]")
ID_RE = re.compile(r"^[A-Z]\d{1,2}$")


def _files():
    files = sorted((ROOT / "data" / "knowledge").glob("*.md"))
    files += [ROOT / "research-brief.md", ROOT / "flood-problems.md"]
    return [f for f in files if f.exists()]


def corpus_signature() -> tuple:
    return tuple((f.name, f.stat().st_mtime_ns) for f in _files())


def _clean(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\(https?://[^)]*\)", r"\1", s)
    s = URL_RE.sub("", s)
    s = re.sub(r"\s*[;,]\s*\)", ")", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = EMOJI_RE.sub("", s).replace("**", "").replace("*", "")
    s = re.sub(r"\[(?:UNVERIFIED|CONFLICTING)\]", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ;,.()")
    return re.sub(r"^[A-Z]\.\s+", "", s)


def _row_text(cells: list[str]) -> str:
    """Table row -> sentence: drop ID cells, rating cells, and source cells."""
    keep = []
    for c in cells:
        c = c.strip()
        if not c or ID_RE.match(c) or EMOJI_RE.search(c) or URL_RE.search(c):
            continue
        keep.append(_clean(c).rstrip("."))
    return ". ".join(k for k in keep if k) + "."


def _research_sections(text: str) -> str:
    """research-brief: keep only section 1 (FLOODING); air/heat sections are dropped."""
    m1 = text.find("## 1.")
    m2 = text.find("## 2.")
    return text[m1:m2] if m1 >= 0 and m2 > m1 else text


def _pick_source(credit: str, urls: list[str]) -> str:
    """Match a parenthetical credit like '(NHESS 2018)' to the card source URL that mentions it."""
    for tok in re.findall(r"[a-z]{4,}", credit.lower()):
        for u in urls:
            if tok in re.sub(r"[^a-z]", "", u.lower()):
                return u
    return urls[0] if urls else ""


def _knowledge_chunks(f) -> list[dict]:
    """Cards: '# title', 'source:' lines, '- fact (credit)' bullets, and a 'What to do:' paragraph."""
    lines = f.read_text(encoding="utf-8").splitlines()
    title = _clean(lines[0].lstrip("# ")) if lines else f.stem
    urls = [m.group(0).rstrip(".") for l in lines if l.lower().startswith("source:") for m in [URL_RE.search(l)] if m]
    out = []
    for l in lines[1:]:
        l = l.strip()
        if not l or l.lower().startswith("source:") or l.startswith("#"):
            continue
        inline = URL_RE.findall(l)
        if l.startswith("-"):
            body, kind = l.lstrip("- "), "fact"
        elif l.lower().startswith("what to do:"):
            body, kind = l[len("what to do:"):], "action"
        else:
            continue
        credit = re.search(r"\(([^()]*)\)\s*$", _clean(body) if False else body)
        src = inline[0].rstrip(".") if inline else _pick_source(credit.group(1) if credit else "", urls)
        text = _clean(body)
        text = re.sub(r"\s*\([^()]{1,60}\)\s*\.?$", ".", text) if kind == "fact" else text
        if len(text) > 30 and src:
            out.append({"title": title, "text": text.strip(), "source": src, "file": f.name, "kind": kind})
    return out


def _file_chunks(f) -> list[dict]:
    if f.parent.name == "knowledge":
        return _knowledge_chunks(f)
    text = f.read_text(encoding="utf-8")
    if f.name == "research-brief.md":
        text = _research_sections(text)
    out, title, buf = [], f.stem, []
    last_url = ""
    file_url = (URL_RE.findall(text) or [f.name])[0]
    knowledge = f.parent.name == "knowledge"

    def flush():
        body = _clean("\n".join(buf))
        if len(body) >= 40 and (knowledge or file_url.startswith("http")):
            urls = URL_RE.findall("\n".join(buf))
            src = (urls[0] if urls else (file_url if knowledge else "")).rstrip(".")
            for i in range(0, len(body), 900):
                if not src:
                    break
                out.append({"title": _clean(title), "text": body[i:i + 900], "source": src, "file": f.name, "kind": "fact"})

    for line in text.splitlines():
        m = HEAD_RE.match(line)
        if m:
            flush()
            title, buf = m.group(2), []
        elif line.lstrip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            if all(re.fullmatch(r"[\s:\-]*", c) for c in cells):
                continue
            if len(cells) < 3 or cells[0].strip() in ("#", "Event"):
                continue
            urls = URL_RE.findall(line)
            if urls:
                last_url = urls[0].rstrip(".")
            elif "same" in line.lower():
                pass  # reuse last_url
            else:
                last_url = ""
            body = _row_text(cells)
            if len(body) >= 30 and last_url:
                out.append({"title": _clean(title), "text": body, "source": last_url, "file": f.name, "kind": "fact"})
        else:
            buf.append(line)
    flush()
    return out


def load_chunks() -> list[dict]:
    chunks = []
    for f in _files():
        chunks += _file_chunks(f)
    return chunks


def _embed(texts: list[str]) -> np.ndarray | None:
    import time as _t
    if not gemini_key() or _t.time() < _embed_off_until:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key())
        out = []
        if not texts:
            return None
        for i in range(0, len(texts), 90):
            r = client.models.embed_content(
                model=embed_model(),
                contents=texts[i : i + 90],
                config=types.EmbedContentConfig(output_dimensionality=EMBED_DIM),
            )
            out += [e.values for e in r.embeddings]
            from . import telemetry
            telemetry.embed_call(len(texts[i:i + 90]), sum(len(t) for t in texts[i:i + 90]))
        v = np.array(out, dtype=np.float32)
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
    except Exception as e:  # noqa: BLE001  (429 or any failure: callers use BM25-only search)
        _embed_failed(e)
        return None


def _embed_failed(e: Exception) -> None:
    from .config import is_quota_error
    global _embed_off_until
    if is_quota_error(e):
        import time as _t
        _embed_off_until = _t.time() + 300  # skip embedding calls briefly; BM25 serves the query


_embed_off_until = 0.0


def _cached_embeddings(chunks: list[dict]) -> np.ndarray | None:
    h = hashlib.sha1((embed_model() + "".join(c["title"] + c["text"] for c in chunks)).encode()).hexdigest()[:16]
    path = BACKEND / ".cache" / f"emb_{h}.npy"
    if path.exists():
        return np.load(path)
    v = _embed([c["title"] + ". " + c["text"] for c in chunks])
    if v is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, v)
    return v


class Index:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.bm25 = BM25Okapi([_tok(c["title"] + " " + c["text"]) for c in chunks]) if chunks else None
        self.vecs = _cached_embeddings(chunks) if chunks else None
        self.pg = None
        if self.vecs is not None and database_url().startswith("postgres"):
            self.pg = self._init_pg()

    # --- pgvector (optional) ---
    def _init_pg(self):
        try:
            from sqlalchemy import create_engine, text

            url = sqlalchemy_url()
            eng = create_engine(url)
            with eng.begin() as c:
                c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                c.execute(text(f"CREATE TABLE IF NOT EXISTS ai_chunks (id int PRIMARY KEY, text text, source text, embedding vector({EMBED_DIM}))"))
                c.execute(text("DELETE FROM ai_chunks"))
                for i, (ch, v) in enumerate(zip(self.chunks, self.vecs)):
                    c.execute(
                        text("INSERT INTO ai_chunks VALUES (:i,:t,:s,CAST(:e AS vector))"),
                        {"i": i, "t": ch["title"] + ". " + ch["text"], "s": ch["source"], "e": str(v.tolist())},
                    )
            return eng
        except Exception:
            return None

    def _vector_scores(self, query: str) -> np.ndarray | None:
        if self.vecs is None:
            return None
        q = _embed([query])
        if q is None:
            return None
        if self.pg is not None:
            try:
                from sqlalchemy import text

                with self.pg.connect() as c:
                    rows = c.execute(
                        text("SELECT id, 1 - (embedding <=> CAST(:e AS vector)) FROM ai_chunks ORDER BY embedding <=> CAST(:e AS vector) LIMIT 20"),
                        {"e": str(q[0].tolist())},
                    ).all()
                s = np.zeros(len(self.chunks))
                for i, sc in rows:
                    s[i] = sc
                return s
            except Exception:
                pass
        return self.vecs @ q[0]

    def search(self, query: str, k: int = 4) -> list[dict]:
        if not self.chunks:
            return []
        bm = np.array(self.bm25.get_scores(_tok(query)))
        bm = bm / bm.max() if bm.max() > 0 else bm
        vs = self._vector_scores(query)
        score = bm if vs is None else 0.4 * bm + 0.6 * np.clip(vs, 0, 1)
        boost = np.array([KNOWLEDGE_BOOST if c["file"] != "flood-problems.md" and c["file"] != "research-brief.md" else 0 for c in self.chunks])
        score = np.where(score > 0, score + boost, 0)
        top = np.argsort(-score)[:k]
        return [
            {"kind": self.chunks[i]["kind"], "file": self.chunks[i]["file"], "title": self.chunks[i]["title"], "text": self.chunks[i]["text"], "source": self.chunks[i]["source"], "score": float(score[i])}
            for i in top
            if score[i] > 0
        ]


_index: Index | None = None
_sig: tuple | None = None


def get_index() -> Index:
    """Rebuild lazily when the corpus file set or mtimes change."""
    global _index, _sig
    sig = corpus_signature()
    if _index is None or sig != _sig:
        _index, _sig = Index(load_chunks()), sig
    return _index


def search(query: str, k: int = 4) -> list[dict]:
    try:
        return get_index().search(query, k)
    except Exception:
        return []


def search_adaptive(query: str, kmin: int = 2, kmax: int = 4, rel: float = 0.6) -> list[dict]:
    """Top-k between kmin and kmax: near-duplicate chunks removed, weak matches (< rel x best score) dropped."""
    out, seen = [], set()
    for h in search(query, kmax + 3):
        key = re.sub(r"\W+", "", h["text"].lower())[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    if not out:
        return []
    top = out[0]["score"]
    return [h for i, h in enumerate(out) if i < kmin or h["score"] >= rel * top][:kmax]


_qemb: dict[str, np.ndarray] = {}


def embed_query(text: str) -> np.ndarray | None:
    """Normalized embedding of one short text (memoized), or None without a key / on error."""
    t = (text or "").strip()[:500]
    if t in _qemb:
        return _qemb[t]
    v = _embed([t])
    if v is None:
        return None
    if len(_qemb) > 2000:
        _qemb.clear()
    _qemb[t] = v[0]
    return v[0]


def card_chunk(file: str, kind: str, contains: str = "") -> dict | None:
    """First chunk of a knowledge card by kind ('action'|'fact'), optionally containing a keyword."""
    try:
        for c in get_index().chunks:
            if c["file"] == file and c["kind"] == kind and contains.lower() in c["text"].lower():
                return c
    except Exception:
        pass
    return None
