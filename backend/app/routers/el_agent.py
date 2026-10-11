import asyncio
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/el-agent", tags=["el-agent"])


def _signed_url(agent_id: str, key: str) -> str:
    from elevenlabs.client import ElevenLabs
    c = ElevenLabs(api_key=key)
    return c.conversational_ai.conversations.get_signed_url(agent_id=agent_id).signed_url


@router.get("/signed-url")
async def signed_url():
    agent_id = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not agent_id:
        return JSONResponse({"detail": "ELEVENLABS_AGENT_ID not set; run scripts/create_el_agent.py"}, status_code=503)
    if not key:
        return JSONResponse({"detail": "ELEVENLABS_API_KEY not set"}, status_code=503)
    try:
        url = await asyncio.to_thread(_signed_url, agent_id, key)
    except Exception as e:
        msg = str(e)
        hint = " (API key may lack the convai/conversational AI permission)" if "401" in msg or "403" in msg or "permission" in msg.lower() else ""
        return JSONResponse({"detail": f"ElevenLabs signed URL failed{hint}: {msg[:200]}"}, status_code=503)
    return {"signed_url": url}
