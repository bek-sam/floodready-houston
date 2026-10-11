import base64
import hashlib
import hmac

from tests.test_api import client  # noqa: F401  (reuses the mocked-network fixture)


def sim(c, body, frm="+15550001"):
    r = c.post("/api/sms/simulate", json={"from": frm, "body": body})
    assert r.status_code == 200
    return r.json()["reply"]


def test_zip_reply(client):
    r = sim(client, "77096")
    assert len(r) <= 459 and "911" in r and "FEMA zone X" in r and "Harvey" in r and "flood alerts" in r


def test_ayuda_zip_spanish(client):
    r = sim(client, "AYUDA 77096", "+15550002")
    assert "911" in r and "Zona FEMA" in r and "peligro" in r


def test_help_and_stop_compliance(client):
    assert "STOP" in sim(client, "HELP", "+15550003")
    assert "unsubscribed" in sim(client, "STOP", "+15550003")
    assert sim(client, "77096", "+15550003") == ""  # silent until START
    assert "welcome back" in sim(client, "START", "+15550003")


def test_alerts_on_off_stores_optin(client):
    from app.db import get_session
    from app.services.sms import SmsOptIn
    assert "ZIP" in sim(client, "ALERTS ON", "+15550004")
    r = sim(client, "ALERTS ON 77096", "+15550004")
    assert "ON" in r and "STOP" in r and "rates" in r
    with get_session() as s:
        assert s.get(SmsOptIn, "+15550004").opted_in is True
    assert "OFF" in sim(client, "ALERTS OFF", "+15550004")
    with get_session() as s:
        assert s.get(SmsOptIn, "+15550004").opted_in is False


def test_inbound_twiml(client):
    r = client.post("/api/sms/inbound", content="From=%2B15550005&Body=77096",
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200 and r.text.startswith("<?xml") and "<Message>" in r.text


def test_signature_only_when_token_set(client, monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok")
    h = {"content-type": "application/x-www-form-urlencoded"}
    assert client.post("/api/sms/inbound", content="From=%2B1555&Body=help", headers=h).status_code == 403
    url = "http://testserver/api/sms/inbound"
    sig = base64.b64encode(hmac.new(b"tok", (url + "Body" + "help" + "From" + "+1555").encode(), hashlib.sha1).digest()).decode()
    assert client.post("/api/sms/inbound", content="From=%2B1555&Body=help", headers={**h, "x-twilio-signature": sig}).status_code == 200


def test_checkin(client, monkeypatch):
    for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM"):
        monkeypatch.delenv(k, raising=False)
    s = client.get("/api/checkin/script?lang=es").json()
    assert s["lang"] == "es" and "1" in s["digits"] and "2" in s["digits"] and "<Gather" in s["twiml"]
    assert client.post("/api/checkin/call", json={"phone": "+15550006", "name": "A", "lang": "en"}).status_code == 503


def test_simulate_storm_prefix_and_warning(client):
    j = client.post("/api/sms/simulate", json={"from": "+15550010", "body": "77096", "simulate": True}).json()
    r = j["reply"]
    assert j["simulated"] is True and r.startswith("[SIMULATED - demo only]")
    assert "Warning" in r and "SIMULATED" in r and "911" in r and len(r) <= 459


def test_simulate_omitted_unchanged(client):
    j = client.post("/api/sms/simulate", json={"from": "+15550011", "body": "77096"}).json()
    assert j["simulated"] is False and "SIMULATED" not in j["reply"]


def test_simulate_help_unchanged(client):
    j = client.post("/api/sms/simulate", json={"from": "+15550012", "body": "HELP", "simulate": True}).json()
    assert "SIMULATED" not in j["reply"] and "STOP" in j["reply"] and j["simulated"] is False


def test_inbound_ignores_simulate(client):
    r = client.post("/api/sms/inbound", content="From=%2B15550013&Body=77096&simulate=1",
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200 and "SIMULATED" not in r.text


def test_danger_texts_get_911_first():
    from app.services.sms import is_danger
    for body in ["help me we are stuck in the attic", "Estamos atrapados, el agua sube", "cuu toi nuoc dang len", "water rising can't get out"]:
        assert is_danger(body), body
    for body in ["77096", "HELP", "ALERTS ON 77096", "AYUDA 77096", "5300 N Braeswood Blvd"]:
        assert not is_danger(body), body
