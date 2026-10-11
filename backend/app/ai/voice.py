"""/voice: ElevenLabs multilingual TTS -> mp3 bytes, cached on disk by hash(text+lang+voice+model)."""
import hashlib
import os

from .config import BACKEND

CACHE = BACKEND / ".cache" / "voice"


def has_key() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY", "").strip())


def synthesize(text: str, lang: str = "en") -> bytes:
    voice = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    model = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")
    text = text[:2500]
    path = CACHE / (hashlib.sha256(f"{text}|{lang}|{voice}|{model}".encode()).hexdigest()[:24] + ".mp3")
    if path.exists():
        return path.read_bytes()
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"].strip())
    audio = b"".join(client.text_to_speech.convert(
        voice_id=voice, text=text, model_id=model, output_format="mp3_44100_128"))
    if not audio:
        raise RuntimeError("empty audio from ElevenLabs")
    if audio:
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)
    return audio


FILLERS = {"en": "One moment...", "es": "Un momento...", "vi": "Xin chờ một chút...", "zh": "请稍等...", "ar": "لحظة من فضلك..."}


def _cache_path(text: str, lang: str, voice: str, model: str):
    return CACHE / (hashlib.sha256(f"{text}|{lang}|{voice}|{model}".encode()).hexdigest()[:24] + ".mp3")


def stream_synthesize(text: str, lang: str = "en"):
    """Yield mp3 chunks from ElevenLabs streaming TTS; cache the full clip when complete."""
    voice = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    model = "eleven_flash_v2_5"
    text = text[:2500]
    path = _cache_path(text, lang, voice, model)
    if path.exists():
        yield path.read_bytes()
        return
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"].strip())
    parts = []
    for chunk in client.text_to_speech.stream(voice_id=voice, text=text, model_id=model, output_format="mp3_44100_128"):
        if chunk:
            parts.append(chunk)
            yield chunk
    if parts:
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"".join(parts))


def filler_audio(lang: str = "en") -> bytes:
    """One cached localized 'one moment' clip per language."""
    lang = lang if lang in FILLERS else "en"
    return synthesize(FILLERS[lang], lang)
