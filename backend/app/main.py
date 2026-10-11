import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from fastapi import APIRouter, FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.config import key_flags  # noqa: E402
from app.db import init_db  # noqa: E402
from app.ratelimit import RateLimitMiddleware  # noqa: E402
from app.routers import alerts, civic, crossings, geocode, insurance, replay, reports, risk, route, watch, push, shelters, outlook, gauges, zipinsurance, medical, floodhistory, buyouts, el_agent, sms, status, evac  # noqa: E402

@asynccontextmanager
async def lifespan(_):
    init_db()
    log = logging.getLogger("main")
    tasks: list[asyncio.Task] = []
    for modname, fn in (("push", "loop"), ("gauge_history", "poll_loop"), ("zipinsurance", "preseed")):
        try:
            mod = __import__(f"app.services.{modname}", fromlist=[fn])
            tasks.append(asyncio.create_task(getattr(mod, fn)(), name=f"{modname}.{fn}"))
        except Exception as e:
            log.warning("%s.%s not started: %s", modname, fn, e)
    try:
        yield
    finally:
        for t in tasks:
            t.cancel()
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2)
        except asyncio.TimeoutError:
            log.warning("background tasks did not stop within 2s")


app = FastAPI(title="FloodReady Houston API", lifespan=lifespan)
_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()] or [
    "http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(RateLimitMiddleware)
app.add_middleware(  # added last = outermost, so 429/422 responses still carry CORS headers
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"], allow_headers=["*"],
)

api = APIRouter(prefix="/api")


@api.get("/health")
async def health():
    return {"status": "ok", "keys": key_flags()}


for m in (geocode, risk, alerts, crossings, route, replay, insurance, reports, civic, watch, push, shelters, outlook, gauges, zipinsurance, medical, floodhistory, buyouts, el_agent, sms, status, evac):
    api.include_router(m.router)
from app.routers import harvey as _harvey_router  # noqa: E402
api.include_router(_harvey_router.router)
from app.routers import hwm as _hwm_router, coastal as _coastal_router  # noqa: E402
api.include_router(_hwm_router.router)
api.include_router(_coastal_router.router)

try:
    from app.ai.router import router as ai_router  # type: ignore
    api.include_router(ai_router)
except ImportError as e:  # AI agent's module may not exist yet
    logging.getLogger("main").warning("AI router not loaded: %s", e)

try:
    from app.ai.live_router import router as live_router  # type: ignore
    api.include_router(live_router)
except Exception as e:  # live engine written by another agent
    logging.getLogger("main").warning("live router not loaded: %s", e)

app.include_router(api)
