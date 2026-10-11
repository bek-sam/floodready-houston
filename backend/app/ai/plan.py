"""/plan: personalised preparedness steps. Gemini JSON when keyed, else templates."""
import json
import re

from .config import gemini_key, gemini_models, is_model_not_found

WHEN = ("now", "storm_watch", "storm", "after")


ES = {  # English title -> (título, detalle) for Spanish households
    "Know your higher risk": ("Conozca su mayor riesgo", "Su ubicación está en una zona de alto riesgo o terreno bajo. Planee una ruta de salida que evite los pasos a desnivel."),
    "Build a go-bag": ("Prepare una mochila de emergencia", "Agua, comida para 3 días, linterna, cargador de teléfono y copias de identificaciones y papeles del seguro en una bolsa impermeable."),
    "Check flood insurance": ("Revise el seguro contra inundaciones", "Las pólizas normales de casa y de inquilino suelen excluir inundaciones. El seguro NFIP tarda 30 días en empezar; compre antes de la temporada de tormentas."),
    "Renters: get renters + flood coverage": ("Inquilinos: seguro de inquilino e inundación", "La póliza del dueño no cubre sus pertenencias. Fotografíe sus cosas y tenga el contrato a mano."),
    "Medical supplies": ("Suministros médicos", "Tenga 7 días o más de medicinas y una lista de dosis y médicos. Pregunte a su farmacia sobre surtidos de emergencia."),
    "Dialysis plan": ("Plan de diálisis", "Pida a su clínica su plan de emergencia y un centro alterno. Programe una sesión extra antes de la tormenta y siga la dieta de emergencia renal."),
    "Backup power": ("Energía de respaldo", "Avise a su compañía eléctrica que depende de equipo médico y cargue baterías de respaldo."),
    "Mobility plan": ("Plan de movilidad", "Arregle ahora un transporte y un ayudante, porque las calles pueden cerrar rápido. Planee salir temprano a un lugar más alto y accesible; no espere el rescate. Llame al 911 si no puede salir con seguridad."),
    "No car? Line up a ride": ("¿Sin carro? Consiga transporte", "Acuerde con un vecino o familiar cómo salir, y averigüe el refugio y el transporte público más cercanos. Llame al 311 o al 211 para ayuda."),
    "Pets": ("Mascotas", "Empaque comida, medicinas, transportadora y cartilla de vacunas. Confirme dónde aceptan mascotas antes de salir."),
    "Watch alerts": ("Vigile las alertas", "Revise las alertas de weather.gov para su dirección. Una Advertencia de Inundación Repentina significa actuar ya."),
    "Turn around, don't drown": ("Dé la vuelta, no se ahogue", "Nunca maneje ni camine por agua de inundación. La mayoría de las muertes por inundación en Texas ocurren en vehículos. Si queda atrapado, llame al 911."),
    "Move to higher ground": ("Suba a un lugar alto", "Vaya al nivel seguro más alto. Evite áticos sin salida al techo. Llame al 911 en emergencias que amenacen la vida."),
    "After the flood": ("Después de la inundación", "Fotografíe los daños antes de limpiar, evite el agua de inundación y presente pronto sus reclamos al seguro y a FEMA."),
}


def template_plan(profile: dict, risk: dict | None = None) -> list[dict]:
    steps = _template_en(profile, risk)
    lang = ((profile or {}).get("language") or "en").lower()
    if lang == "es":
        steps = [{**x, "title": ES.get(x["title"], (x["title"], ""))[0], "detail": ES.get(x["title"], ("", x["detail"]))[1]}
                 for x in steps if x["title"] != "Language help"]
        steps.append({"title": "Ayuda en español", "detail": "Pida un intérprete gratis al llamar al 311 o al 911 y diga que habla español.", "when": "now"})
    elif lang != "en":
        steps.append({"title": "Plan shown in English", "detail": f"This plan is in English for now ('{lang}' translation coming). Ask a friend or call 211 for help reading it.", "when": "now"})
    return steps


def _template_en(profile: dict, risk: dict | None = None) -> list[dict]:
    p = profile or {}
    s = []
    add = lambda title, detail, when: s.append({"title": title, "detail": detail, "when": when})
    risk = risk if isinstance(risk, dict) and "error" not in (risk or {}) else {}
    if risk.get("sfha") or risk.get("low_ground"):
        add("Know your higher risk", "Your location is in a high-risk flood area or low ground. Plan an exit route that avoids underpasses.", "now")
    add("Build a go-bag", "Water, 3 days of food, flashlight, phone charger, copies of IDs and insurance papers in a waterproof bag.", "now")
    add("Check flood insurance", "Standard homeowner and renter policies usually exclude flood. NFIP policies have a 30-day wait, so buy before storm season.", "now")
    if p.get("renter"):
        add("Renters: get renters + flood coverage", "Your landlord's policy does not cover your belongings. Photograph your things and keep the lease handy.", "now")
    medical = [m.lower() for m in p.get("medical") or []]
    if medical:
        add("Medical supplies", "Keep 7+ days of medication and a list of doses and doctors. Ask your pharmacy about emergency refills.", "now")
    if any("dialysis" in m for m in medical):
        add("Dialysis plan", "Ask your clinic for its emergency plan and an alternate center. Schedule an extra session before the storm and follow the renal emergency diet.", "storm_watch")
    if any(k in m for m in medical for k in ("oxygen", "ventilator", "power")):
        add("Backup power", "Tell your utility you rely on powered medical equipment and charge backup batteries.", "storm_watch")
    if p.get("mobility") and str(p["mobility"]).lower() not in ("none", "full", "normal", ""):
        add("Mobility plan", "Arrange a ride and a helper now, since roads can close fast. Plan to leave early to a higher, accessible place; do not wait for rescue. Call 911 if you cannot get out safely.", "storm_watch")
    if not p.get("has_car", True):
        add("No car? Line up a ride", "Agree with a neighbor or relative on a ride out, and learn the nearest shelter and transit options. Call 311 for help.", "storm_watch")
    if p.get("pets"):
        add("Pets", "Pack food, meds, carrier and vaccine records. Confirm where pets are allowed before you leave.", "storm_watch")
    add("Watch alerts", "Check weather.gov alerts for your address. A Flash Flood Warning means act now.", "storm_watch")
    add("Turn around, don't drown", "Never drive or walk into floodwater. Most Texas flood deaths happen in vehicles. If trapped, Call 911.", "storm")
    add("Move to higher ground", "Go to the highest safe level. Avoid attics with no roof exit. Call 911 for life-threatening emergencies.", "storm")
    add("After the flood", "Photograph damage before cleaning, stay out of floodwater, and file insurance and FEMA claims promptly.", "after")
    lang = (p.get("language") or "en").lower()
    if lang != "en":
        add("Language help", f"Request interpretation in '{lang}' when calling 311 or 911; many services offer free interpreters.", "now")
    return s


def gemini_plan(profile: dict, risk: dict | None) -> list[dict] | None:
    if not gemini_key():
        return None
    try:
        from google import genai
        from google.genai import types

        prompt = (
            "Make a short flood-preparedness plan (6-10 steps) for this Houston household. "
            "Return JSON array of {title, detail, when} where when is one of now|storm_watch|storm|after. "
            "Use plain language in the household's language. Do not invent statistics. "
            "Emergencies: say Call 911. Not official guidance.\n"
            f"Profile: {json.dumps(profile)}\nRisk data: {json.dumps(risk, default=str)[:3000]}")
        client = genai.Client(api_key=gemini_key())
        r = None
        for model in gemini_models():
            try:
                r = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3))
                break
            except Exception as e:
                if not is_model_not_found(e):
                    return None
        if r is None:
            return None
        raw = (r.text or "").strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
        steps = json.loads(raw)
        if isinstance(steps, dict):
            steps = steps.get("steps") or steps.get("plan") or []
        steps = [{"title": str(x["title"]), "detail": str(x["detail"]),
                  "when": x["when"] if x.get("when") in WHEN else "now"}
                 for x in steps if isinstance(x, dict) and x.get("title") and x.get("detail")]
        return steps or None
    except Exception:
        return None


def make_plan(profile: dict, risk: dict | None = None) -> dict:
    steps = gemini_plan(profile, risk)
    if steps:
        return {"steps": steps, "generated_by": "gemini"}
    return {"steps": template_plan(profile, risk), "generated_by": "template"}
