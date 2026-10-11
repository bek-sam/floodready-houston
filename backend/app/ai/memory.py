"""Household profile store: SQLite/Postgres table `ai_profiles` (source of truth).
When BACKBOARD_API_KEY is set, the profile is also pushed to a Backboard assistant (best effort)."""
import json
import os
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


def save_profile(profile: dict) -> dict:
    profile = dict(profile)
    profile["id"] = profile.get("id") or uuid.uuid4().hex[:12]
    with _eng().begin() as c:
        row = c.execute(select(_table).where(_table.c.id == profile["id"])).first()
        aid = _backboard_sync(profile, row.backboard_assistant_id if row else None)
        values = {"data": json.dumps(profile), "backboard_assistant_id": aid}
        if row:
            c.execute(_table.update().where(_table.c.id == profile["id"]).values(**values))
        else:
            c.execute(_table.insert().values(id=profile["id"], **values))
    return profile


def get_profile(pid: str) -> dict | None:
    with _eng().connect() as c:
        row = c.execute(select(_table).where(_table.c.id == pid)).first()
    return json.loads(row.data) if row else None
