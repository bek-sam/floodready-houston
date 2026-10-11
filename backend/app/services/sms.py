"""SMS / voice check-in channel for people without smartphones or data.

Pure logic lives here; routers/sms.py is a thin HTTP layer. Nothing in this module
sends a real SMS or call: replies are returned as text/TwiML for Twilio to deliver
(or for the in-app simulator to display). Outbound calls need TWILIO_* env.
"""
import asyncio
import base64
import hashlib
import hmac
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from html import escape

from sqlalchemy import Boolean, Column, DateTime, Float, String

from app.db import Base, get_session
from app.services.alerts import get_alerts, is_flood_alert
from app.services.geo import geocode
from app.services.risk import get_risk

log = logging.getLogger("sms")
MAX_CHARS = 459  # 3 concatenated GSM-7 segments (153 each); replies are kept ASCII


class SmsOptIn(Base):
    __tablename__ = "sms_optins"
    phone = Column(String(32), primary_key=True)
    label = Column(String(200), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    lang = Column(String(8), default="en")
    opted_in = Column(Boolean, default=False)
    stopped = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# Common Houston ZIP centroids so the demo works offline; others fall back to the geocoder.
ZIPS = {
    "77096": (29.6770, -95.4830, "77096"), "77002": (29.7589, -95.3677, "77002"),
    "77004": (29.7253, -95.3585, "77004"), "77025": (29.6910, -95.4325, "77025"),
    "77074": (29.6860, -95.5160, "77074"), "77036": (29.6985, -95.5380, "77036"),
    "77055": (29.7966, -95.4936, "77055"), "77024": (29.7706, -95.5188, "77024"),
    "77079": (29.7723, -95.5961, "77079"), "77077": (29.7490, -95.6000, "77077"),
    "77489": (29.6190, -95.5260, "77489"), "77449": (29.8350, -95.7340, "77449"),
    "77379": (30.0100, -95.5320, "77379"), "77338": (29.9890, -95.2680, "77338"),
}

STR = {
    "en": {
        "zone": "FEMA zone {z}", "nozone": "FEMA zone unknown",
        "hv_y": "Flooded in Harvey", "hv_n": "Not in Harvey extent (not proof it stayed dry)", "hv_u": "Harvey data n/a here",
        "al_n": "No active flood alerts", "al_y": "ACTIVE: {e}",
        "act_alert": "Move to higher ground; never drive through water.",
        "act_risk": "Check flood insurance and plan a route now.",
        "act_low": "Keep a go-bag ready and text ALERTS ON {z} for alerts.",
        "c911": "Call 911 if in danger.",
        "ask": "FloodReady: text a Houston ZIP or street address for your flood risk. Text HELP for options.",
        "nf": "FloodReady: could not find that place. Text a Houston ZIP (e.g. 77096) or full street address.",
        "help": "FloodReady: text a ZIP or address for flood risk. ALERTS ON <ZIP> = alerts, ALERTS OFF, STOP = unsubscribe. Msg&data rates may apply. Call 911 if in danger.",
        "on": "FloodReady: flood alerts ON for {p}. Msg&data rates may apply. Reply ALERTS OFF or STOP to cancel, HELP for help.",
        "on_need": "FloodReady: to turn alerts on, text ALERTS ON plus your ZIP (e.g. ALERTS ON 77096).",
        "off": "FloodReady: flood alerts OFF. Text ALERTS ON <ZIP> any time to resume.",
        "stop": "FloodReady: you are unsubscribed and will get no more texts. Text START to resume.",
        "start": "FloodReady: welcome back. Text a ZIP or address for flood risk.",
        "stopped": "", "err": "FloodReady: service is busy. Text again soon. Call 911 if in danger.",
    },
    "es": {
        "zone": "Zona FEMA {z}", "nozone": "Zona FEMA desconocida",
        "hv_y": "Se inundo en Harvey", "hv_n": "Fuera del area de Harvey (no garantiza que no se inundo)", "hv_u": "Sin datos de Harvey aqui",
        "al_n": "Sin alertas de inundacion activas", "al_y": "ACTIVA: {e}",
        "act_alert": "Suba a terreno alto; nunca maneje por el agua.",
        "act_risk": "Revise su seguro de inundacion y planee su ruta ya.",
        "act_low": "Tenga una mochila lista y envie ALERTAS SI {z} para alertas.",
        "c911": "Llame al 911 si esta en peligro.",
        "ask": "FloodReady: envie un ZIP o direccion de Houston para ver su riesgo de inundacion. Envie AYUDA para opciones.",
        "nf": "FloodReady: no encontre ese lugar. Envie un ZIP de Houston (ej. 77096) o la direccion completa.",
        "help": "FloodReady: envie un ZIP o direccion para ver el riesgo. ALERTAS SI <ZIP> = alertas, ALERTAS NO, STOP = cancelar. Pueden aplicar tarifas de msj y datos. Llame al 911 si esta en peligro.",
        "on": "FloodReady: alertas de inundacion ACTIVADAS para {p}. Pueden aplicar tarifas. Responda ALERTAS NO o STOP para cancelar, AYUDA para ayuda.",
        "on_need": "FloodReady: para activar alertas envie ALERTAS SI y su ZIP (ej. ALERTAS SI 77096).",
        "off": "FloodReady: alertas DESACTIVADAS. Envie ALERTAS SI <ZIP> para reanudar.",
        "stop": "FloodReady: se cancelo su suscripcion y no recibira mas mensajes. Envie START para reanudar.",
        "start": "FloodReady: bienvenido de nuevo. Envie un ZIP o direccion.",
        "stopped": "", "err": "FloodReady: servicio ocupado. Intente pronto. Llame al 911 si esta en peligro.",
    },
    "vi": {
        "zone": "Vung FEMA {z}", "nozone": "Chua ro vung FEMA",
        "hv_y": "Bi ngap khi bao Harvey", "hv_n": "Ngoai vung ngap Harvey (khong co nghia la chua tung ngap)", "hv_u": "Khong co du lieu Harvey",
        "al_n": "Khong co canh bao lu dang hieu luc", "al_y": "DANG CO: {e}",
        "act_alert": "Di chuyen len cho cao; dung bao gio lai xe qua nuoc.",
        "act_risk": "Kiem tra bao hiem lu lut va lap lo trinh ngay.",
        "act_low": "Chuan bi tui khan cap va nhan ALERTS ON {z} de nhan canh bao.",
        "c911": "Goi 911 neu nguy hiem.",
        "ask": "FloodReady: nhan ma ZIP hoac dia chi o Houston de xem nguy co lu. Nhan GIUP de xem lenh.",
        "nf": "FloodReady: khong tim thay dia diem. Nhan ZIP Houston (vd 77096) hoac dia chi day du.",
        "help": "FloodReady: nhan ZIP hoac dia chi de xem nguy co lu. ALERTS ON <ZIP> = canh bao, ALERTS OFF, STOP = huy. Co the tinh phi tin nhan/du lieu. Goi 911 neu nguy hiem.",
        "on": "FloodReady: da BAT canh bao lu cho {p}. Co the tinh phi. Nhan ALERTS OFF hoac STOP de huy, GIUP de tro giup.",
        "on_need": "FloodReady: de bat canh bao, nhan ALERTS ON kem ZIP (vd ALERTS ON 77096).",
        "off": "FloodReady: da TAT canh bao. Nhan ALERTS ON <ZIP> de bat lai.",
        "stop": "FloodReady: ban da huy dang ky, se khong nhan them tin. Nhan START de tiep tuc.",
        "start": "FloodReady: chao mung tro lai. Nhan ZIP hoac dia chi.",
        "stopped": "", "err": "FloodReady: he thong ban. Thu lai sau. Goi 911 neu nguy hiem.",
    },
}

SCRIPT = {
    "en": {"say": "This is FloodReady Houston checking on you. Are you safe? Press 1 if you are safe. Press 2 if you need help and we will notify your emergency contact. If you are in danger, hang up and call 9 1 1.",
           "yes": "Thank you. Stay safe. Goodbye.", "help": "We are notifying your emergency contact now. If you are in danger, hang up and call 9 1 1.",
           "none": "We did not get a response. If you need help, call 9 1 1.", "voice": "Polly.Joanna", "language": "en-US"},
    "es": {"say": "Le habla FloodReady Houston para saber de usted. Esta a salvo? Oprima 1 si esta a salvo. Oprima 2 si necesita ayuda y avisaremos a su contacto de emergencia. Si esta en peligro, cuelgue y llame al 9 1 1.",
           "yes": "Gracias. Cuidese. Adios.", "help": "Estamos avisando a su contacto de emergencia ahora. Si esta en peligro, cuelgue y llame al 9 1 1.",
           "none": "No recibimos respuesta. Si necesita ayuda, llame al 9 1 1.", "voice": "Polly.Lupe", "language": "es-US"},
    "vi": {"say": "Day la FloodReady Houston hoi tham ban. Ban co an toan khong? Nhan 1 neu an toan. Nhan 2 neu can giup do va chung toi se bao nguoi lien lac khan cap cua ban. Neu nguy hiem, hay cup may va goi 9 1 1.",
           "yes": "Cam on ban. Hay giu an toan. Tam biet.", "help": "Chung toi dang bao nguoi lien lac khan cap cua ban. Neu nguy hiem, hay cup may va goi 9 1 1.",
           "none": "Chung toi khong nhan duoc phan hoi. Neu can giup do, hay goi 9 1 1.", "voice": "Polly.Joanna", "language": "vi-VN"},
}


def _ascii(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s: str) -> str:
    return " ".join(_ascii(s).lower().split())


_ES = re.compile(r"\b(ayuda|alertas?|hola|inundacion|direccion|si|activar|desactivar|calle|donde|riesgo|cuidese)\b")
_VI = re.compile(r"\b(giup|tro giup|lu lut|ngap|canh bao|xin chao|dia chi|bat|tat|nguy co)\b")


def detect_lang(body: str, default: str = "en") -> str:
    raw = body.lower()
    if re.search(r"[ơưăâêôđạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", raw):
        return "vi"
    if re.search(r"[¿¡ñ]", raw):
        return "es"
    n = norm(body)
    if _VI.search(n):
        return "vi"
    if _ES.search(n):
        return "es"
    return default


def clip(text: str) -> str:
    t = _ascii(text)
    return t if len(t) <= MAX_CHARS else t[:MAX_CHARS - 3].rstrip() + "..."


def twiml(msg: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(msg)}</Message></Response>' if msg else \
        '<?xml version="1.0" encoding="UTF-8"?><Response/>'


# ---------- Twilio signature ----------

def twilio_configured() -> bool:
    return bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("TWILIO_FROM"))


def valid_signature(url: str, params: dict, signature: str | None) -> bool:
    """X-Twilio-Signature check. Only enforced when TWILIO_AUTH_TOKEN is set."""
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not token:
        return True
    if not signature:
        return False
    data = url + "".join(k + params[k] for k in sorted(params))
    mac = base64.b64encode(hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(mac, signature)


# ---------- storage ----------

def _store(phone: str):
    s = get_session()
    Base.metadata.create_all(s.get_bind(), tables=[SmsOptIn.__table__])
    return s


def _get(s, phone: str) -> SmsOptIn:
    row = s.get(SmsOptIn, phone)
    if not row:
        row = SmsOptIn(phone=phone, opted_in=False, stopped=False)
        s.add(row)
    return row


# ---------- parsing ----------

_ZIP = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
_ON = {"on", "si", "activar", "activa", "bat"}
_OFF = {"off", "no", "desactivar", "desactiva", "tat"}


def parse_command(body: str) -> tuple[str, str]:
    """Returns (cmd, rest). cmd in stop|start|help|on|off|query|empty."""
    n = norm(body)
    if not n:
        return "empty", ""
    w = n.split()
    first = w[0].strip(".,!?")
    if first in ("stop", "stopall", "unsubscribe", "cancel", "end", "quit", "parar", "cancelar", "huy"):
        return "stop", ""
    if first in ("start", "unstop", "yes", "unirse"):
        return "start", ""
    if first in ("help", "ayuda", "info", "giup", "?", "menu") or n in ("tro giup", "giup do"):
        rest = n.split(None, 1)[1] if len(w) > 1 else ""
        if n.startswith("tro giup"):
            rest = n[8:].strip()
        return "help", rest
    if first in ("alerts", "alert", "alertas", "alerta", "canh"):
        rest = w[1:]
        if first == "canh" and rest[:1] == ["bao"]:
            rest = rest[1:]
        if rest and rest[0] in _ON:
            return "on", " ".join(rest[1:])
        if rest and rest[0] in _OFF:
            return "off", ""
        return "help", ""
    return "query", body.strip()


async def resolve_place(text: str) -> tuple[float, float, str] | None:
    text = text.strip()
    m = _ZIP.search(text)
    if m and len(re.sub(r"[\d\s-]", "", text)) < 3:  # message is basically just a ZIP
        z = m.group(1)
        if z in ZIPS:
            return ZIPS[z]
        g = await geocode(z + " TX")
        if g.get("lat") is not None:
            return g["lat"], g["lon"], z
        return None
    q = text if re.search(r"\b(tx|texas)\b", text.lower()) else f"{text}, Houston, TX"
    g = await geocode(q)
    if g.get("lat") is None:
        if m and m.group(1) in ZIPS:
            return ZIPS[m.group(1)]
        return None
    label = (g.get("matched_address") or text).title()
    return g["lat"], g["lon"], label[:60]


async def summarize(lat: float, lon: float, label: str, lang: str) -> str:
    S = STR[lang]
    risk, alerts = await asyncio.gather(get_risk(lat, lon), get_alerts(lat, lon), return_exceptions=True)
    risk = risk if isinstance(risk, dict) else {}
    flood = [a for a in (alerts.get("alerts", []) if isinstance(alerts, dict) else []) if is_flood_alert(a)]
    zone = risk.get("fema_zone")
    hv = (risk.get("harvey") or {}).get("flooded")
    parts = [S["zone"].format(z=zone) if zone else S["nozone"],
             S["hv_y"] if hv is True else S["hv_n"] if hv is False else S["hv_u"],
             S["al_y"].format(e=flood[0].get("event") or "flood") if flood else S["al_n"]]
    if flood:
        act = S["act_alert"]
    elif hv is True or risk.get("sfha") or risk.get("low_ground"):
        act = S["act_risk"]
    else:
        act = S["act_low"].format(z=label.split()[0] if label[:5].isdigit() else "77096")
    return clip(f"{label}: " + ". ".join(parts) + f". {act} {S['c911']}")


# ---------- main entry ----------

async def handle(phone: str, body: str) -> str:
    """Returns the plain-text reply ('' = send nothing)."""
    phone = (phone or "unknown")[:32]
    cmd, rest = parse_command(body)
    with _store(phone) as s:
        row = _get(s, phone)
        lang = detect_lang(body, row.lang or "en") if cmd not in ("stop", "start") else (row.lang or "en")
        if cmd in ("help", "on", "off", "query", "empty") and lang != row.lang and body.strip():
            row.lang = lang
        S = STR[lang]
        row.updated_at = datetime.now(timezone.utc)
        if cmd == "stop":
            row.stopped, row.opted_in = True, False
            s.commit()
            return S["stop"]
        if cmd == "start":
            row.stopped = False
            s.commit()
            return S["start"]
        if row.stopped:  # compliance: no replies after STOP until START
            s.commit()
            return ""
        if cmd in ("empty",):
            s.commit()
            return S["ask"]
        if cmd == "help":
            s.commit()
            if rest and _ZIP.search(rest):
                pass  # "AYUDA 77096": help text plus risk summary below
            else:
                return clip(S["help"])
        if cmd == "off":
            row.opted_in = False
            s.commit()
            return S["off"]
        try:
            if cmd == "on" and not rest.strip():
                if row.lat is None:
                    s.commit()
                    return S["on_need"]
                row.opted_in = True
                s.commit()
                return clip(S["on"].format(p=row.label or "your area"))
            place = await resolve_place(rest if cmd in ("on", "help") else body)
            if not place:
                s.commit()
                return S["nf"]
            lat, lon, label = place
            row.lat, row.lon, row.label = lat, lon, label
            if cmd == "on":
                row.opted_in = True
                s.commit()
                return clip(S["on"].format(p=label))
            s.commit()
            summary = await summarize(lat, lon, label, lang)
            if cmd == "help":
                return clip(summary)
            return summary
        except Exception as e:  # never leave a texter without a 911 line
            log.warning("sms handle failed: %s", e)
            s.rollback()
            return S["err"]


# ---------- voice check-in ----------

def checkin_script(lang: str) -> dict:
    lang = lang if lang in SCRIPT else "en"
    c = SCRIPT[lang]
    return {"lang": lang, "say": c["say"], "digits": {"1": c["yes"], "2": c["help"]}, "no_response": c["none"],
            "voice": c["voice"], "language": c["language"], "action": "POST /api/checkin/digit",
            "twiml": checkin_twiml(lang)}


def checkin_twiml(lang: str, action: str = "/api/checkin/digit") -> str:
    c = SCRIPT.get(lang, SCRIPT["en"])
    return ('<?xml version="1.0" encoding="UTF-8"?><Response>'
            f'<Gather numDigits="1" timeout="8" action="{escape(action)}?lang={lang}" method="POST">'
            f'<Say voice="{c["voice"]}" language="{c["language"]}">{escape(c["say"])}</Say></Gather>'
            f'<Say voice="{c["voice"]}" language="{c["language"]}">{escape(c["none"])}</Say></Response>')


def digit_twiml(lang: str, digit: str) -> str:
    c = SCRIPT.get(lang, SCRIPT["en"])
    msg = c["yes"] if digit == "1" else c["help"] if digit == "2" else c["none"]
    if digit == "2":
        log.warning("check-in: caller pressed 2 (needs help); emergency contact should be notified")
    return (f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="{c["voice"]}" language="{c["language"]}">'
            f'{escape(msg)}</Say></Response>')
