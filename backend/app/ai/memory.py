"""Household profile store: SQLite/Postgres table `ai_profiles` (source of truth).
When BACKBOARD_API_KEY is set, the profile is also pushed to a Backboard assistant (best effort).

Access: creating a profile returns a random secret `token` (only its SHA-256 is stored, in `ai_profile_tokens`).
Reading or overwriting a profile needs that token. Legacy profiles saved before tokens existed have no token row:
they can no longer be read or overwritten through the API (safer than read-only: a guessed id leaks nothing)."""
import hashlib
import hmac
import json
import os
import secrets
import uuid

import httpx
from sqlalchemy import Column, MetaData, String, Table, Text, create_engine, select

from .config import sqlalchemy_url

BB = "https://app.backboard.io/api"
_meta = MetaData()
_table = Table("ai_profiles", _meta,
               Column("id", String(64), primary_key=True),
               Column("data", Text, nullable=False),
               Column("backboard_assistant_id", String(64)))
_tokens = Table("ai_profile_tokens", _meta,  # separate table: no ALTER on existing ai_profiles
                Column("id", String(64), primary_key=True),
                Column("token_hash", String(64), nullable=False))
_engine = None


def _eng():
    global _engine
    if _engine is None:
        url = sqlalchemy_url()
        _engine = create_engine(url)
        _meta.create_all(_engine)
    return _engine


def _backboard_sync(profile: dict, assistant_id: str | None) -> str | None:
    key = os.getenv("BACKBOARD_API_KEY", "").strip()
    if not key:
        return assistant_id
    h = {"X-API-Key": key}
    try:
        with httpx.Client(timeout=10) as c:
            if not assistant_id:
                r = c.post(f"{BB}/assistants", headers=h, json={
                    "name": f"floodready-{profile['id'][:8]}",
                    "system_prompt": "Remember this household's flood-preparedness profile."})
                r.raise_for_status()
                assistant_id = r.json()["assistant_id"]
            t = c.post(f"{BB}/assistants/{assistant_id}/threads", headers=h, json={})
            t.raise_for_status()
            c.post(f"{BB}/threads/{t.json()['thread_id']}/messages", headers=h, data={
                "content": "Household profile (remember): " + json.dumps(profile),
                "memory": "Auto", "stream": "false"}).raise_for_status()
    except Exception:
        pass
    return assistant_id


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def check_token(pid: str, token: str | None) -> bool:
    """True only if the profile has a token row and `token` matches it (legacy profiles have none)."""
    if not token:
        return False
    with _eng().connect() as c:
        row = c.execute(select(_tokens).where(_tokens.c.id == pid)).first()
    return bool(row) and hmac.compare_digest(row.token_hash, _hash(token))


def save_profile(profile: dict, token: str | None = None) -> dict:
    """Create (new random id + token, returned once as profile['token']) or overwrite an existing id with its token.
    An unknown client-chosen id is ignored and a fresh id is issued. Raises PermissionError on a bad token."""
    profile = {k: v for k, v in profile.items() if k != "token"}
    new_token = None
    with _eng().begin() as c:
        row = c.execute(select(_table).where(_table.c.id == profile.get("id"))).first() if profile.get("id") else None
        if row is not None:
            tok = c.execute(select(_tokens).where(_tokens.c.id == row.id)).first()
            if not (token and tok and hmac.compare_digest(tok.token_hash, _hash(token))):
                raise PermissionError("profile token required")
        else:
            profile["id"] = uuid.uuid4().hex[:12]
            new_token = secrets.token_urlsafe(24)
            c.execute(_tokens.insert().values(id=profile["id"], token_hash=_hash(new_token)))
        aid = _backboard_sync(profile, row.backboard_assistant_id if row else None)
        values = {"data": json.dumps(profile), "backboard_assistant_id": aid}
        if row:
            c.execute(_table.update().where(_table.c.id == profile["id"]).values(**values))
        else:
            c.execute(_table.insert().values(id=profile["id"], **values))
    return {**profile, **({"token": new_token} if new_token else {})}


def get_profile(pid: str) -> dict | None:
    with _eng().connect() as c:
        row = c.execute(select(_table).where(_table.c.id == pid)).first()
    return json.loads(row.data) if row else None
