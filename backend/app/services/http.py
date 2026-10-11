"""Shared async HTTP helper with a tiny TTL cache. Never raises: returns None on failure."""
import logging
import time

from app import freshness

import httpx

from app.config import HTTP_TIMEOUT, USER_AGENT

log = logging.getLogger("http")
_cache: dict = {}


def cache_get(key, max_age: float | None = None):
    hit = _cache.get(key)
    if hit and hit[0] > time.time():
        if max_age is not None and time.time() - hit[2] > max_age:
            return None
        return hit[1]
    return None


def cache_set(key, value, ttl: float):
    _cache[key] = (time.time() + ttl, value, time.time())
    if len(_cache) > 2000:
        _cache.clear()


async def get_json(url: str, params: dict | None = None, ttl: float = 300, headers: dict | None = None):
    key = (url, tuple(sorted((params or {}).items())))
    ttl = freshness.effective_ttl(url, ttl)  # storm mode caps TTL for alert/gauge/risk hosts
    cached = cache_get(key, ttl if ttl <= freshness.STORM_TTL else None) if ttl > 0 else None
    if cached is not None:
        return cached
    src, t0 = freshness.source_for(url), time.time()
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True,
                                     headers={"User-Agent": USER_AGENT, **(headers or {})}) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        freshness.record(src, True, (time.time() - t0) * 1000)
        if ttl > 0:
            cache_set(key, data, ttl)
        return data
    except Exception as e:
        freshness.record(src, False, (time.time() - t0) * 1000, type(e).__name__)
        log.warning("GET %s failed: %s", url, e)
        return None
