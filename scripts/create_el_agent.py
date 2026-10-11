#!/usr/bin/env python3
"""Create the FloodReady ElevenLabs Conversational AI agent.

Usage: python scripts/create_el_agent.py [--dry-run] [--lang en] [--voice VOICE_ID]
Prints only the new agent id plus .env instructions. --dry-run prints the config.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PROMPT = (
    "You are FloodReady Houston's voice assistant. Answer ONLY from tool results and retrieved context; "
    "if they do not cover the question, say you don't know. Call tools with the user's lat/lon or zip when known. "
    "If someone is in danger, tell them to call 911 first. Keep answers to 1-3 short spoken sentences, "
    "plain speech, no markdown or URLs. End important guidance with 'Not official guidance.'"
)
FIRST = "Hi, I'm FloodReady Houston. Ask me about flood risk, insurance, alerts, or what to do. If you're in danger, call 911."

_P = {
    "lat": {"type": "number", "description": "Latitude"},
    "lon": {"type": "number", "description": "Longitude"},
    "zip": {"type": "string", "description": "5-digit ZIP code"},
    "query": {"type": "string", "description": "Search query"},
}
TOOLS = {
    "get_risk": ("Get flood risk for a location.", ["lat", "lon"]),
    "get_flood_history": ("Get past flood history near a location.", ["lat", "lon"]),
    "get_zip_insurance": ("Get flood insurance info for a ZIP code.", ["zip"]),
    "get_alerts": ("Get active flood alerts near a location.", ["lat", "lon"]),
    "get_medical": ("Get nearby medical/dialysis facilities and flood exposure.", ["lat", "lon"]),
    "search_knowledge": ("Search the FloodReady knowledge cards.", ["query"]),
}


def build_config(lang: str, voice: str) -> dict:
    tools = []
    for name, (desc, keys) in TOOLS.items():
        tools.append({
            "type": "client", "name": name, "description": desc, "expects_response": True,
            "response_timeout_secs": 15,
            "parameters": {"type": "object", "properties": {k: {**_P[k]} for k in _P},
                           "required": []},
        })
    return {
        "agent": {"first_message": FIRST, "language": lang,
                  "prompt": {"prompt": PROMPT, "llm": "gemini-2.5-flash", "tools": tools}},
        "tts": {"voice_id": voice, "model_id": "eleven_flash_v2_5"},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--voice", default=os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"))
    a = ap.parse_args()
    cfg = build_config(a.lang, a.voice)
    if a.dry_run:
        print(json.dumps({"name": "FloodReady Houston", "conversation_config": cfg}, indent=2))
        return 0
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key:
        print("ELEVENLABS_API_KEY is not set", file=sys.stderr)
        return 1
    from elevenlabs.client import ElevenLabs
    from elevenlabs.types import ConversationalConfig
    try:
        r = ElevenLabs(api_key=key).conversational_ai.agents.create(
            name="FloodReady Houston", conversation_config=ConversationalConfig(**cfg))
    except Exception as e:
        m = str(e)
        if "missing_permissions" in m or "convai" in m.lower() or "401" in m or "403" in m or "permission" in m.lower():
            print("ERROR: this API key lacks the Conversational AI (convai_write) permission. "
                  "Enable it in ElevenLabs > Developers > API Keys, then retry.\n" + m[:300], file=sys.stderr)
        else:
            print("ERROR creating agent: " + m[:500], file=sys.stderr)
        return 1
    print(r.agent_id)
    print(f"Add to .env:\nELEVENLABS_AGENT_ID={r.agent_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
