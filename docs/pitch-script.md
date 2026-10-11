# FloodReady Houston: full pitch script

Lines in plain text are what you **say**. Lines starting with ▶ are what you **do** (click, type, switch).

Total: about 4 minutes, as 1:15 of slides, 2:15 of live demo and 0:30 to close. If you only get 2 minutes, use the **Short version** at the end.

---

## Before you walk up (5 minutes earlier)

▶ Laptop on power, Wi-Fi connected, phone charged, volume up.
▶ Backend running **without** auto-reload: `cd backend && uv run uvicorn app.main:app --port 8000`
▶ Warm the caches: `cd backend && uv run python ../scripts/prewarm.py http://localhost:8000`
▶ Check: `backend/.venv/bin/python scripts/demo_check.py` → **21/21 passed**
▶ Browser tab 1: the pitch deck (Present mode, slide 1).
▶ Browser tab 2: `http://localhost:5173/?demo=1#home` (shows the "Demo mode" badge). Set the place to `5300 N Braeswood Blvd, Houston, TX 77096` and make sure **Simulate storm is OFF**.
▶ Browser tab 3: `http://localhost:5173/?demo=1#drive`
▶ Allow the microphone once on the Ask page, so the permission prompt doesn't interrupt the demo.

---

## Part 1: The problem (slides 1–4, about 75 seconds)

### Slide 1: "Half the homes Harvey flooded were never on the map"
Let me start with the problem.

In Hurricane Harvey, 154,170 homes in Harris County flooded. Only 36 percent of them had flood insurance, and nearly half were outside the mapped floodplain. Those families did everything the map told them to, and they still flooded.

And the biggest killer isn't the house. 77 percent of Texas flood deaths came from people driving into water.

### Slide 2: "What the research says"
This isn't our opinion; it's the research.

A peer-reviewed study of Harvey found that 81 percent of the deaths were drownings, "particularly in and around vehicles". A UTHealth study found that 77 percent of Texas flood deaths came from driving into water, and Harris County leads the state.

Rice University found that the vast majority of at-risk homes have no flood insurance, and that if one storm shifts just a few miles, the number of flooded homes can grow from about 3,600 to more than 13,000. Rainfall rates in Harris County are up more than 30 percent, but the flood maps in force predate that. And the Army Corps has rated our two big reservoir dams at high risk of failure.

### Slide 3: "63 Houston flood problems, in 7 groups"
So we did the research properly. We catalogued 63 concrete Houston flood problems in seven groups: drivers in flooded roads, maps that give false safety, insurance, warnings that arrive too late, vulnerable people, infrastructure, and recovery.

Every problem has a definition and its sources. We're honest about one group, infrastructure and funding: that's policy, and no app fixes a dam, so we make it visible instead.

### Slide 4: "Today's tools show gauges and 2007 maps, not you"
Here's the gap. Today's tools show river gauges and flood maps, not you. Risk, alerts, roads, insurance and recovery help are spread across a dozen websites, mostly in English.

---

## Part 2: Introducing FloodReady (slide 5, about 10 seconds)

### Slide 5: "FloodReady Houston"
That's why I built FloodReady Houston. It turns any Houston address into a plain-language flood answer, in five languages, with a route check and an AI assistant you can talk to. It isn't a new warning system: it's a layer on top of the official sources (FEMA, NOAA, the county), put together for the people they miss.

Let me show you, live.

▶ Switch to **browser tab 2** (Home).

---

## Part 3: Live demo (about 2 minutes 15 seconds)

### Demo 1: Know your risk (about 30 seconds)
▶ Home is showing `5300 N Braeswood Blvd` in Meyerland. If it isn't: tap **Set my place** → type the address → pick it → the sheet closes.

This is a real address in Meyerland. In one screen, FloodReady shows what official tools publish separately, side by side.

▶ Point at the summary chips.

FEMA zone AE, which is high risk, right next to "flooded in Harvey". And in this ZIP code, 6,482 flood insurance claims, from FEMA's own data.

▶ Scroll to **Live conditions** → nearby gauges → open **"What this level means"** on Brays Bayou.

This is the live Brays Bayou gauge. Instead of a number in feet, it tells you what that level means for your street, and how high Harvey got.

▶ Expand **"Flood history here"**.

And it's the history: Harvey was a major flood here. Every fact you see links to its public source: FEMA, NOAA, the City of Houston.

### Demo 2: Drive safe (about 35 seconds)
▶ Switch to **browser tab 3** (Drive).

Now the part that saves lives, because driving is what kills people.

▶ Tap the chip **"Downtown: Allen Parkway underpass"**.
▶ Turn on the **Simulate storm** toggle (it is clearly labelled as a demo).
▶ Tap **Check route**.

I'm simulating a storm, and the app labels it as a simulation so it never passes for real data. Now I check a drive downtown.

▶ The red **"Avoid this route"** verdict appears with named crossings.

"Avoid this route." It names the exact flood-prone crossings, including the Allen Parkway underpass, and says why. When there's a better option, it suggests a detour with fewer flood-prone spots and the extra minutes. And it will never tell you a road is "safe": the best it says is "no known flood-prone crossings".

▶ Turn **Simulate storm OFF** again.

### Demo 3: Ask, in Spanish (about 30 seconds)
▶ Go to **Ask**. Switch the language to **Español** (the EN menu, top right).
▶ Type or tap: **"¿Qué hago si mi calle se inunda?"**

Houston is one of the most diverse cities in America, and flood help is mostly in English. So I'll ask in Spanish: "What do I do if my street floods?"

▶ The answer appears with numbered citations and a 911 line.

It answers in Spanish, with a citation on every sentence, and it always starts with 911 when there's danger.

▶ Open **"How I answered"** under the answer.

And this is the agent at work. It understood the question, searched our sourced knowledge, called live data tools, and you can see exactly which sources it used. No black box.

### Demo 4: Talk to it (about 25 seconds, optional if time allows)
▶ Switch **Type / Talk** to **Talk** → tap the mic → hold to talk.
▶ Say: **"Did my neighborhood flood before?"**

Or just talk to it.

▶ It answers out loud in about a second and a half.

It already knows my address, and I can interrupt it like a real conversation.

▶ If voice stalls: tap **Retry**, or **Switch to typing**. Don't wait more than 5 seconds.

### Demo 5: Built for everyone (about 15 seconds; pick ONE)
- **Option A, offline:** ▶ open `#offline`. "And when the power and internet go out in a storm, this safety card still works: your zone, your household's needs, 911, 311 and 211."
- **Option B, after the flood:** ▶ open **After a flood**. "After the water goes down: whether FEMA aid is actually open, the 60-day insurance claim deadline, how to appeal a denial, and how to avoid scams."

▶ Switch back to **browser tab 1** (the deck), slide 10.

---

## Part 4: Proof, model, close (slides 10–12, about 40 seconds)

### Slide 10: "We tried to disprove ourselves"
We didn't grade ourselves on vibes. Three reviewers checked all 52 original problems against the code, with a live test for each one. The app reduces harm for 33 of them, and fully solves 5. That honest audit actually lowered our own earlier count, and the bugs it found were fixed the same morning.

240 automated tests pass. The AI scores 38 out of 40 on our safety evaluation in five languages, and 15 out of 15 on citations. Every number is dated and linked on the app's Judge page.

### Slide 11: "Free for residents, paid by institutions"
Residents never pay. The institutions that already own this problem do: city and county emergency management, property managers who are legally required to give tenants flood notices, and dialysis outreach programs. We will never sell resident data.

Next is a 90-day pilot in three neighborhoods.

### Slide 12: "The next storm will come"
The next storm will come. FloodReady makes sure every Houstonian's answer is ready: their address, their route, their language.

Thank you. I'm happy to take questions, or you can try it on your phone right now.

(Slide 13, References, stays hidden unless someone asks "where is this from?")

---

## If something goes wrong

| Problem | What you do | What you say |
|---|---|---|
| A page is slow (over 3 s) | Wait, don't refresh | "This is pulling live data from FEMA and NOAA right now." |
| The route doesn't show "Avoid" | Check that Simulate storm is ON, then Check route again | "Let me turn on the simulated storm." |
| Voice doesn't answer | **Switch to typing**, ask the same question | "Same agent, typed." |
| Ask is slow or Gemini errors | Wait; it falls back automatically | "Even without the AI, it answers from our sourced knowledge." |
| Wi-Fi dies | Stop the backend, then run `cd backend && DEMO_SNAPSHOT=1 uv run uvicorn app.main:app --port 8000` | "We built an offline demo mode for exactly this." (The banner says "Offline demo data".) |
| A judge asks for a number you don't know | Open the **Judge page** (`#judge`) → Evidence | "Every number is dated and linked here." |

---

## Likely judge questions: short answers

- **"Doesn't this already exist?"** The pieces do, and we say so. FEMA has the zones, the county has gauges, NWS and ReadyHarris send alerts, First Street scores risk on Zillow, and TranStar has road sensors. We didn't find any one place for Houston that puts them together for your address, in five languages, with a route check, a cited assistant and recovery steps. NYC's FloodChat is a multilingual flood assistant, so the idea is proven elsewhere; Houston doesn't have one. We're a layer on top of the official tools, not a replacement (`docs/competition.md`).
- **"Is the data live?"** Yes. FEMA, NOAA, NWS, USGS and OpenFEMA, live with caching. Every screen shows how fresh its data is, and anything historical is labelled. The 2017 shelter list says it's historical.
- **"How do you know it works?"** A problem-by-problem audit with a live test each: 33 of 52 reduced, 5 fully. It's in `docs/problems/`, and the Judge page has the dated numbers.
- **"What does the AI actually do?"** It's a LangGraph agent with retrieval over sourced knowledge and 16 live data tools. It cites every sentence, its numbers are checked against the sources, and the "How I answered" panel shows what it used.
- **"What if the AI is wrong?"** Numbers that aren't in a source are removed. Every emergency answer says 911. Everything is labelled "not official guidance". Without an API key, it falls back to sourced templates.
- **"Who pays?"** Not residents. Emergency management, property managers, health outreach and grants.
- **"What can't it do?"** Fix dams or funding, which is policy. The Harvey flood-extent data covers only the City of Houston. The crossing list has 128 entries and isn't complete. The Vietnamese, Chinese and Arabic translations still need native-speaker review.
- **"Is it deployed?"** It's deploy-ready with Docker Compose and Caddy, and the scripts are in `deploy/`. Today it runs locally. *(If you deployed by then: give the URL and the QR code on the Judge page.)*

---

## Short version (2 minutes)

Slides 1–2 (30 s): Harvey flooded 154,170 homes; only 36% were insured; nearly half were outside the floodplain; 77% of Texas flood deaths are drivers. The research backs this.
Slide 3 (10 s): We catalogued 63 problems in seven groups.
Slide 5 (5 s): FloodReady turns your address into a plain-language answer in your language.
▶ Demo 1 (20 s): Meyerland: Zone AE plus "flooded in Harvey" plus 6,482 claims.
▶ Demo 2 (25 s): Allen Parkway + simulated storm → "Avoid this route", with named crossings.
▶ Demo 3 (20 s): Spanish question → cited answer → "How I answered".
Slide 10 (10 s): A strict audit: reduces harm for 33 of 52 problems, 240 tests, every number on the Judge page.
Slide 12 (10 s): The next storm will come. Your answer should be ready. Thank you.
