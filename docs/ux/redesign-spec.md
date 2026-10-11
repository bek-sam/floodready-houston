# FloodReady Houston: Redesign Spec (v1)

Owner: design lead. Audience: builder agents. Scope: `frontend/` only, except where noted in §8.4.
Goal: make FloodReady feel like a credible civic product. One saved place, one clear answer at the top of Home, calm visuals, plain language, and no demo controls in front of real users.

Ground rules carried over from `CLAUDE.md`:
- Every fact shown carries a source link. Do not add new statistics. Every number on screen comes from an API field or from an existing i18n string that already has a source.
- Emergency copy says "Call 911". AI copy says "not official guidance".
- Every feature works without keys. Every new screen has loading, empty, error and offline states.
- en is the reference language. es must reach parity for every new string, in the same PR. vi/zh/ar fall back to en through `tr()`. That is acceptable, but list the missing keys in the PR.

---

## 1. Audit

Screenshots are in `docs/ux/before/`. **Filename note:** the files after 06 are off by one. `07-drive.jpg` is a duplicate of Replay, `08-prepare.jpg` shows Drive, `09-recover.jpg` shows Prepare, `10-ask.jpg` shows Recover. `03-home-renting.jpg` duplicates `02`. **No Ask screenshot exists**, so the Ask audit below comes from `pages/Ask.tsx`. The round floating "brain" button at bottom right in every shot is a browser extension, not our app. Ignore it.

Severity: **C** = critical (blocks trust or task), **M** = major, **m** = minor.

### 1.1 Global shell (every screenshot, `App.tsx`, `index.css`)
| # | Problem | Sev | Evidence |
|---|---|---|---|
| G1 | **No visual identity.** The plain text "FloodReady Houston" is the only brand mark. Colors are the Tailwind defaults (a light-blue active pill on dark navy). It looks like a template. | M | 00, 05–10 |
| G2 | **Emoji and Unicode glyphs used as icons** (⌂ ◉ ▶ ➤ ✔ ✚ ?, 🔔 🔊 🎤 ⚠ ✖ ◆). They render differently per OS, mix weights, and screen readers may announce them. ✚ ("Recover") reads as "medical", and ▶ ("Replay") and ➤ ("Drive") are near-identical. | M | 00, 05 |
| G3 | **Sidebar labels are centered** while icons are left-aligned, so the eye zig-zags. There is no grouping and no section labels. | m | 00, 05 |
| G4 | **The 911 bar is a salmon/red alarm strip** (`bg-danger`) that is always on. It reads as an active emergency on a calm day (alarm fatigue), and in dark mode its text is the page bg color on #ff8a80. It should be calm, high-contrast and permanent, and turn red only when there is real danger. | M | all |
| G5 | **Seven bottom tabs on mobile** (`grid-cols-7`, 11px labels, `truncate`). That is too many for one thumb. Spanish labels ("Repetición", "Recuperar", "Preguntar") will truncate. | C | App.tsx |
| G6 | **No persistent "my place".** `place` is `useState(null)` in App, so it is lost on reload, and Watch, Drive, Prepare and Recover each ask for their own address. Recover silently falls back to downtown (`HOUSTON`), so shelter distances are wrong. Prepare's plan falls back to downtown coordinates. | C | 05, 08, 09; ctx.tsx |
| G7 | **Header is empty on desktop**: three utility controls float right with nothing else (no title, no place, no page context). On mobile the app name takes the whole bar. | m | 00 |
| G8 | **Page titles are inconsistent:** "Know your real flood risk", "Flood Watch", "Storm replay", "Drive safe", "Prepare", "Recover and hold accountable". Nav labels differ from the titles ("My Risk" vs "Know your real flood risk", "Drive Safe" vs "Drive safe"). | m | all |
| G9 | **Ad-hoc colors and status glyphs:** `bg-red-600` on Talk, hard-coded `#0b5cad` and `#fff` on maps, a separate `CAT_ICON` map in Home that duplicates `STATUS_ICON`, and an inline-styled SW update toast (`#0f172a`/`#38bdf8`) that ignores the theme. | m | ui.tsx, Home.tsx, main.tsx |
| G10 | **Loading is text only** ("Loading…"). There are no skeletons, so layout jumps as cards arrive in random order (risk, alerts, outlook and history load independently). | M | Home.tsx |
| G11 | **Footer disclaimer is 12px muted text** at the very bottom of long pages, where nobody sees it. | m | 00 |
| G12 | **Offline banner copy uses an em dash and appears above the header**, which pushes content down. It is fine in principle. | m | App.tsx |

### 1.2 Home / My Risk (00, 01, 02, 04)
| # | Problem | Sev |
|---|---|---|
| H1 | **No answer at the top.** After the lookup, the first thing below the address is "No risk shown today does not mean safe…" (a negation, in muted text), then "Tonight's rain risk: None", then an **empty "Active alerts" card**. The decisive facts sit below the fold: "This location flooded in Harvey (2017)", Zone AE, and ZIP 77096's 6,482 claims. A user who stops after one screen learns "nothing is happening". | C |
| H2 | **A wall of equal-weight cards:** Harvey, FEMA, What really happened, Flood history, Nearest gauges + map, Reservoir, Jurisdiction, Renting or buying (chart + checklist), Before you rent or buy. Every card has the same border, padding and title size, so there is no hierarchy. | C |
| H3 | **The address form stays at full size after a lookup** and the label is repeated as plain text under it. In 01 the matched address shows in ALL CAPS ("5300 N BRAESWOOD BLVD…"), which reads like a database echo. | M |
| H4 | **The CTA says "Check my risk"** and the same `check` key is reused on Prepare's insurance date (see P1). | M |
| H5 | **Inline source links run into the text** ("…expected)NOAA WPC" with no space, in 01). Some source labels are hostnames ("Source: geogimsms.houstontx.gov") and others are friendly names ("OpenFEMA NFIP"). | M |
| H6 | **Content is duplicated:** Harvey appears three times (red callout, "What really happened", "Flood history here"). ZIP claims appear twice ("most NFIP flood claims in 2017 (2550 claims)" in history, and "6,482 … 2,610 since 2017" in Renting). | M |
| H7 | **Low-information cards:** "Reservoir area: No" and "Rules that apply (jurisdiction): City of Houston" each take a full card (04). | m |
| H8 | **Gauge rows:** the status chip floats mid-row with irregular alignment, the stage number has no context (38.7 ft compared to what?), and the sparkline caption "stored readings" is jargon (02). | M |
| H9 | **The claims chart has no y-axis**, its 1978/2026 labels sit under a 0-baseline of dots, and its numbers are not localized (04). | m |
| H10 | **Status vocabulary leaks NWS jargon:** "action", "minor", "major" in lowercase chips with no explanation. "action · 56.99 ft" sounds like a call to act. | M |
| H11 | **Empty state (00) is a lone form** on a big dark canvas: no example, no "why", no trust markers (sources, not official guidance), no language prompt. | M |

### 1.3 Watch (05)
| # | Problem | Sev |
|---|---|---|
| W1 | **Three overlapping alert mechanisms** with no explanation of the difference: "Enable push alerts" (Web Push), "Enable notifications" (browser Notification while open), and the spoken in-app poll. Users cannot tell which one they need. | C |
| W2 | **Demo controls are exposed:** "Send test alert", "Simulate storm push", "Simulate storm (demo)" and "Refresh" sit next to the real CTA. | C |
| W3 | **Address retyped again.** "Name: Home" is prefilled, but the address is empty even when Home already has one. | C |
| W4 | **Intro copy is technical:** "every 2 minutes while this app is open". | m |
| W5 | **Level chips "OK / WATCH / WARNING"** are all caps and do not match the Home vocabulary. | m |

### 1.4 Replay (06, 07 duplicate)
| # | Problem | Sev |
|---|---|---|
| R1 | **The map is full of identical green dots** with no legend, and "your place" is not distinguishable at a glance. Play/Narrate sit below the fold, under the map. | M |
| R2 | **The storm picker is a native `<select>`** for 4 items. Four tappable storm cards with dates would be faster and more evocative. | m |
| R3 | **The Harvey fact paragraph is dense** (4 statistics in 2 lines). It is good content but lacks visual emphasis. | m |

### 1.5 Drive (08)
| # | Problem | Sev |
|---|---|---|
| D1 | **"Demo routes" is the first thing on the page** (4 pill buttons), above the user's own From/To fields. | C |
| D2 | **"Simulate storm" is a checkbox in the main form.** A real user can tick it and get a fake "Avoid" verdict. | C |
| D3 | **"From" is not prefilled from My place** unless Home was used in this session. There is no swap button and no "use my location". | M |
| D4 | **The safety line "Turn around, don't drown"** is 14px muted text under the button, the single most important driving message. | M |

### 1.6 Prepare (09)
| # | Problem | Sev |
|---|---|---|
| P1 | **Wrong CTA:** the insurance countdown button says "Check my risk". It should say "See when coverage starts". | C |
| P2 | **The date input defaults to today's date** with no explanation. The card is framed as "If I buy a policy on", which is good, but there is no headline answer. | m |
| P3 | **The household profile lives only here**, separate from Home, and is not reused by Drive, Ask or Watch. "Medical needs (comma separated…)" is a free-text field for a safety-critical input. Dialysis and oxygen should be checkboxes. | M |
| P4 | **"Get alerts (one tap)" is just two external links**, which is a mislabel. | M |
| P5 | **The plan footer "Plan by: template"** exposes internals. | m |
| P6 | **No STEAR / 211 guidance for people who need help to evacuate**, though it exists in `data/knowledge/special-needs-and-no-car.md` and the README claims it. | M |

### 1.7 Recover (10)
| # | Problem | Sev |
|---|---|---|
| V1 | **The page opens with a 2017 shelter list.** The historical warning is correct, but leading with closed 2017 shelters (Toyota Center "2017 status: Closed") is confusing and undermines trust. | C |
| V2 | **"Recover" and "hold accountable" are mashed together.** A person mopping a flooded house and a person researching bond projects are different jobs in different moments. | M |
| V3 | **The page is very long:** shelters, checklists, tracker, share-911, report form, reports map, bond, reservoir, who's responsible. There is no in-page navigation. | M |
| V4 | **The report form lives here only.** Reporting water on a road is a Drive or Alerts moment, not a recovery one. | M |

### 1.8 Ask (`pages/Ask.tsx`, no screenshot)
| # | Problem | Sev |
|---|---|---|
| A1 | **Empty screen:** a title, a disclaimer, an engine `<select>` and a big "Talk" button, with no suggested questions and no explanation of what Ask knows. | C |
| A2 | **Jargon:** "Voice engine: Fast / Gemini Live (beta) / ElevenLabs Agent (beta)", "Latency → First audio 812 ms (filler) · server 640 ms", "Tools: get_risk, search_knowledge", "via gemini". These are judge or debug details, not user content. | C |
| A3 | **Two mic affordances:** the big Talk button (conversation) and a 🎤 button in the input row (dictation). They are unexplained. | M |
| A4 | **The Talk button turns `bg-red-600` and pulses while listening.** Red means danger in this product, so don't use it for "listening". | M |
| A5 | **Sources render as raw full URLs** with `break-all`. | m |

### 1.9 Judge (`pages/Judge.tsx`)
| # | Problem | Sev |
|---|---|---|
| J1 | **Unreachable except by typing `#judge`.** The checklist is static text and does not deep-link to the steps. | m |
| J2 | **Demo toggles are spread over 3 pages** instead of living here. | M |

### 1.10 Accessibility summary (fix in P6 QA)
- Touch targets ≥44px exist on most buttons. The 11px tab labels and the 32px `<summary>` rows fail. Min target is 44×44 (mobile tab 56px tall).
- Status is conveyed by color plus glyph. Keep a text label always (it already exists in chips). Avoid glyph-only.
- The `aria-live="assertive"` Talk status re-announces on every state change. Use `polite`, except for errors.
- Map markers have no non-map equivalent on Home and Replay (Drive has a text list). Add a text list everywhere.
- Contrast: the 911 strip in dark mode and `text-muted` on `surface-2` must be re-checked against the new tokens (all new tokens in §5.2 are verified ≥4.5:1 for text).

---

## 2. Personas and top jobs

| Persona | Context | Top jobs (in order) | What the app must do |
|---|---|---|---|
| **Rosa**, Spanish-speaking renter, no car, Gulfton apartment | Phone only, prepaid data, reads Spanish best | 1. "Is my building at risk and what do I do?" 2. "How do I get out without a car?" 3. "Does my renters insurance cover flood?" | Language chosen in step 1 of onboarding. "No car" in household → STEAR/211 action in top 3. Ask chips in Spanish. Renter → tenant letter. |
| **David**, adult son; his mother is on dialysis in Meyerland | Manages her safety remotely | 1. Save **her** address, not his. 2. Find backup dialysis centers. 3. Get alerts for her place on his phone. | My place can be "Mom's house". Dialysis checkbox → MedicalAccess in top 3. Watch with multiple places, and push. |
| **Kim**, commuter, during a storm, in the car park | One hand, stressed, glanceable | 1. "Is my route home flooded?" 2. "What's happening right now near me?" | Drive is 1 tap from anywhere. From is prefilled with My place. The verdict is huge, with the reason and a spoken readout. The right-now level is in the Home hero. |
| **Marcus**, homeowner deciding on insurance | Calm day, research mode, desktop | 1. "What is my real risk?" 2. "When would a policy start?" 3. "What do neighbors pay / claim?" | Hero summary with "why" chips and sources. Insurance countdown, ZIP claims and premiums under "Renting or buying" disclosure. |
| **Judge**, 2 minutes, projector + phone | Skims and tests the claims | 1. See the value in 1 screen. 2. See a dramatic "Avoid" and the replay. 3. Hear voice in Spanish. 4. Verify sources. | Judge page with a guided 5-step script that deep-links and sets state. Demo mode badge. Sources visible on every fact. |

Design principle that follows: **one place, one answer, three actions.** Everything else is progressive disclosure.

---

## 3. Information architecture

### 3.1 Primary navigation (mobile bottom bar: exactly 5)
| Order | Label (en / es) | Hash | lucide icon | Contains |
|---|---|---|---|---|
| 1 | **Home** / Inicio | `#home` | `House` | Readiness summary, 3 actions, live conditions, deep details |
| 2 | **Alerts** / Alertas | `#alerts` (alias `#watch`) | `BellRing` | Watched places, push on/off, report flooding |
| 3 | **Drive** / Manejar | `#drive` | `Route` | Route check, crossings map, report water on road |
| 4 | **Prepare** / Prepararse | `#prepare` | `ShieldCheck` | Plan, insurance countdown, help to evacuate, medical, renters |
| 5 | **Ask** / Preguntar | `#ask` | `MessageCircleQuestion` | Type or talk, suggested questions |

### 3.2 Secondary destinations ("More")
These are reached from the header **menu button** (`Menu` icon, label "More" / "Más") on mobile, which opens a right Sheet. On desktop they sit in the sidebar under a "More" group label.
| Label (en / es) | Hash | Icon | Contains |
|---|---|---|---|
| Storm replay / Repetición de tormentas | `#replay` | `History` | Replay, shift-the-storm |
| After a flood / Después de una inundación | `#recover` | `LifeBuoy` | Safety checklists, FEMA aid steps, recovery tracker, share location for 911, historical shelters |
| Who's responsible / Quién es responsable | `#civic` | `Landmark` | Bond tracker, reservoir explainer, who to contact, officials |
| Settings / Ajustes | `#settings` | `Settings` | Language, theme, voice (Standard / Live beta), My place and household, clear my data |
| About & sources / Acerca y fuentes | `#about` | `BookOpen` | What FloodReady is, data sources (from README list), "not official guidance", AI disclosure |
| Judge demo | `#judge` | `Presentation` | Visible only when demo mode is on (§7) |

Old hashes keep working: `#watch`→Alerts. `#recover` keeps the recover content; its civic section moves to `#civic`.

### 3.3 Where every existing feature lives
| Existing feature (file) | New home |
|---|---|
| Address risk card, FEMA zone, elevation, low ground (`Home.tsx`) | Home → hero "why" chips + "Details" disclosure "Your place's flood profile" |
| Harvey flooded (`Home.tsx`) | Home → hero chip + profile disclosure (once only) |
| Flood history (`FloodHistoryCard`) | Home → disclosure "Flood history here" |
| "What really happened" facts | Home → profile disclosure, sub-list "What the FEMA map misses" |
| Nearest gauges + sparkline + map | Home → "Live conditions" section (gauges list) + map in disclosure |
| Rain outlook (`/outlook`) | Home → Live conditions, Outlook tile |
| Active alerts | Home → Live conditions, Alerts tile (an empty alert box renders as a one-line tile, not a card) |
| Reservoir, jurisdiction | Home → profile disclosure, as 2 rows in a key-value list |
| RentBuy (ZIP claims, premiums, buyout area, checklist) (`RentBuy.tsx`) | Home → disclosure "Renting or buying here?" and Prepare → Insurance section links to it |
| Before you rent or buy checklist (`home.c1–c5`) | Inside "Renting or buying here?" |
| Watch places, poll, voice readout (`Watch.tsx`) | Alerts |
| PushCard (`PushCard.tsx`) | Alerts → single "Alerts on this phone" toggle. Test/simulate move to demo mode only |
| Browser Notification permission (Watch) | Folded into the same toggle (request push; on unsupported browsers, fall back to Notification while open) |
| Route check, crossings map/list (`Drive.tsx`) | Drive |
| Demo routes, Simulate storm (Drive) | Demo mode only (§7) |
| Insurance countdown + .ics (`Prepare.tsx`) | Prepare → "Flood insurance" section |
| Household profile + Gemini plan | Profile → onboarding + Settings. Plan → Prepare "Your household plan" |
| MedicalAccess (dialysis finder) | Prepare → "Medical needs" (shown when household has dialysis/oxygen; otherwise collapsed "Find a dialysis center") |
| TenantLetter | Prepare → "Renters" (shown first when household.renter) |
| "Get alerts (one tap)" external links | Prepare → "Official alert systems" (renamed) |
| NEW: Help to evacuate (STEAR, 211) from `data/knowledge/special-needs-and-no-car.md` | Prepare → "If you need help to evacuate" |
| Shelters (historical) (`Recover.tsx`) | After a flood → bottom, collapsed, titled "Shelters used during Harvey (2017): historical" |
| Checklists, RecoveryTracker, Share911 | After a flood (top) |
| Community report form + reports map | Shared `ReportSheet` component, opened from Drive, Alerts and After a flood ("Report flooding") |
| Bond, reservoir, who's responsible, officials (`WhoToContact`) | Who's responsible (`#civic`) |
| Replay + narrate + water tube + shift storm (`Replay.tsx`) | Storm replay |
| Ask + 3 voice engines (`Ask.tsx`, `LiveTalk`, `ElAgentTalk`) | Ask (Standard / Live beta). ElevenLabs Agent appears in demo mode only |
| Judge QR + checklist | Judge (demo mode) |
| Language, theme, install | Header (language globe + install) and Settings |

### 3.4 Global state: `PlaceProvider` (replaces the place part of `ctx.tsx`)
```ts
// src/state/place.tsx
interface Household {
  renter: boolean | null; hasCar: boolean | null
  medical: { dialysis: boolean; oxygen: boolean; powerDevice: boolean; other: string }
  mobility: 'none' | 'some' | 'wheelchair'
  ages: { kids: boolean; older: boolean }   // maps to Profile.age_group: older → 'senior', else 'adult'
  pets: boolean
}
interface MyPlace extends Place { nickname: string; zip: string | null; savedAt: string }
interface PlaceCtx {
  place: MyPlace | null; setPlace(p: MyPlace | null): void
  household: Household; setHousehold(h: Household): void
  onboarded: boolean; finishOnboarding(): void
  demo: boolean; setDemo(on: boolean): void
}
```
- localStorage keys: `floodready.place.v1`, `floodready.household.v1`, `floodready.onboarded.v1`, `floodready.actionsDone.v1` (a map of action id to an ISO date), `floodready.demo` (**sessionStorage**). Every access goes through the existing `try/catch` store helper.
- `zip` comes from `/\b\d{5}\b/` on `matched_address`.
- `toProfile(household, place, lang): Profile` is a pure helper so Prepare, Ask and `/plan` all send the same profile: `medical` = the checked items as strings (`'dialysis'`, `'oxygen'`, `'power device'`, plus `other`); `has_car` = hasCar ?? true; `renter` = renter ?? false.
- The existing `useApp()` keeps `lang`/`t` and re-exports `place`/`setPlace`, so old components keep compiling.

### 3.5 First-run onboarding (`#welcome`, full-screen, skippable)
It shows when `!onboarded` and no `?demo=1`. It is a Stepper with 3 steps and a progress indicator "Step 1 of 3". Each step has a primary button bottom-right, "Back" ghost bottom-left, and a "Skip" text link at top-right.

**Step 1. Language** (title has no translation dependency: show each label in its own language)
- H1: "FloodReady Houston". Sub (en): "Flood safety for your address: risk, alerts, safe routes and a plan. Free, no account." (es: "Seguridad ante inundaciones para su dirección: riesgo, alertas, rutas seguras y un plan. Gratis, sin cuenta.")
- 5 large radio cards (56px tall): English · Español · Tiếng Việt · 中文 · العربية. Selecting one switches `lang` live.
- Footer note (14px): "Not official guidance. In an emergency, call 911."

**Step 2. Your place**
- H1: "Where should we watch?" (es: "¿Qué lugar vigilamos?")
- Sub: "Your home, or the home of someone you look after. We save it on this phone only." (es: "Su casa, o la de alguien que usted cuida. Se guarda solo en este teléfono.")
- Field "Address" with placeholder "e.g. 901 Bagby St, Houston TX". Field "Name this place" uses a Segmented control: Home · Family · Work · Other (Other reveals a text input; default Home). es: Casa · Familia · Trabajo · Otro.
- Primary: "Save place" (es: "Guardar lugar") → geocode → show the matched address in Title Case (`toTitleCase`) with a "Change" link.
- Error: "We couldn't find that address. Try adding the ZIP code, like 77096." (es: "No encontramos esa dirección. Agregue el código postal, por ejemplo 77096.")
- Skip: "Skip for now" → Home shows the empty hero (§4.6).

**Step 3. Your household (optional, 30 seconds)**
- H1: "Who lives there?" (es: "¿Quién vive ahí?") Sub: "This changes your plan and the actions we suggest. Optional." (es: "Esto ajusta su plan y las acciones sugeridas. Opcional.")
- Segmented: "I rent · I own" (Alquilo · Soy dueño).
- Segmented: "Car: Yes · No" (Carro: Sí · No).
- Checkbox group "Anyone who needs…" (¿Alguien necesita…?): Dialysis (Diálisis) · Oxygen (Oxígeno) · A powered medical device (Un equipo médico eléctrico) · Help walking or a wheelchair (Ayuda para caminar o silla de ruedas).
- Checkbox group: Children (Niños) · Adults 65+ (Adultos de 65+) · Pets (Mascotas).
- Primary: "Finish" (Terminar) → `finishOnboarding()`, `POST /profile` fire-and-forget (ignore errors), navigate `#home`.

### 3.6 Header (all screens)
Order left to right. Height 56px, `bg-surface`, bottom border `line`.
1. Brand lockup (§5.1). It is a link to `#home`. On mobile, show the icon plus "FloodReady" only.
2. **My place chip**, the center of the header on mobile and after the lockup on desktop. Pill, height 36, `MapPin` 16px + nickname + "·" + street (truncate at 22ch on mobile) + `ChevronDown`. Aria-label: "My place: Home, 5300 N Braeswood Blvd. Change". Tap opens the **My place Sheet**:
   - Current place card (nickname, full address, "Edit" link).
   - "Change address" field + Save.
   - "Household" summary chips ("Rents · No car · Dialysis") + "Edit household" → the onboarding step 3 form in a Sheet.
   - "Watched places" (from Alerts), each with "Make this My place".
   - When no place is set, the chip reads "Set your place" with a `MapPinPlus` icon and the brand color outline.
3. Right side: demo badge (only in demo), language button (`Languages` icon + 2-letter code, opens a list Sheet), install button (`Download`, only when `beforeinstallprompt` fired, label "Install"), desktop-only theme toggle (`Sun`/`Moon`). On mobile, the menu button (`Menu`, "More") is last.

### 3.7 Desktop layout (≥768px)
- Left sidebar, 240px. Lockup at the top (56px row). Group 1 has no label (Home, Alerts, Drive, Prepare, Ask). Group label "More" (12px uppercase muted, tracking 0.06em) holds Storm replay, After a flood, Who's responsible, Settings, About & sources. Items are 44px tall, **left-aligned** icon 20px + label 15px/500, 12px gap, radius 10. Active = `bg-brand-tint` + `text-brand` + 3px left indicator bar (`inset-inline-start`). No full-color fill.
- Content max width 960px (Home 1040px for 2-column live conditions), gutter 24px.
- Mobile: the bottom bar is 5 equal columns, 64px + safe-area, icon 22px over a 12px/600 label, no truncation (labels fit at 12px in en and es; verify in vi). Active = brand color icon + label + 4px pill indicator above the icon.

---

## 4. Home redesign

### 4.1 Order of content (mobile, top to bottom)
1. **Readiness summary hero** (§4.2)
2. **Do these 3 things now** (§4.4)
3. **Live conditions**: Alerts tile, Rain outlook tile, Nearby gauges list (§4.5)
4. **Details** (collapsed disclosures, each a `Disclosure` row 56px tall with title + one-line preview):
   a. "Your place's flood profile": preview e.g. "Zone AE · Flooded in Harvey · City of Houston rules"
   b. "Flood history here": preview e.g. "4 storms on record at the nearest gauge"
   c. "Renting or buying here?": preview e.g. "ZIP 77096 flood insurance claims and typical premiums"
   d. "Who's responsible here?": a link row to `#civic`
   e. "Replay a past storm here": a link row to `#replay`
5. Trust footer card: "How FloodReady works": "We combine public data from FEMA, NOAA, NWS, USGS, the City of Houston and OpenFEMA. Not official guidance. In an emergency, call 911." + link "All sources" → `#about`.

Desktop: hero full width; under it a 2-column grid (left 7/12 = "Do these 3 things"; right 5/12 = Live conditions); details full width below.

**The address form is removed from Home.** Address entry happens in onboarding and the My place sheet only.

### 4.2 Hero: "Flood readiness summary"
Card `radius-xl`, padding 20 (24 desktop), `bg-surface`, a 4px top border in the **Right-now** level color. Contents in order:

1. Eyebrow (13px/600 muted, uppercase tracking .06em): "FloodReady summary · Home" (nickname).
2. Two side-by-side **level blocks** (stack on <360px):
   - **Right now** (Ahora mismo): RiskBadge (size lg) e.g. "Normal". Under it, a 15px line: the single most important reason (first item from the Right-now rule that fired), e.g. "No flood alerts or high water nearby." / "Flash Flood Warning in effect."
   - **This place** (Este lugar): RiskBadge (lg) "High exposure" / "Elevated exposure" / "Lower exposure". Under it, a 15px line, e.g. "Flooded in Harvey and in a FEMA high-risk zone."
3. **Why chips** (horizontal wrap, 8px gap): one chip per signal that fired, in the order of the rules table. Each chip: icon 14px + short label + tiny `ExternalLink` icon. Tapping a chip opens a **Sheet** with the plain explanation and the SourceLink. Chip labels:
   - "FEMA Zone AE" (a high-risk tint when SFHA)
   - "Flooded in Harvey (2017)"
   - "Major flooding at nearest gauge in Tax Day 2016"
   - "ZIP 77096: 6,482 flood claims" (from `/zip-insurance` `claims.total`)
   - "Low ground for the area"
   - "Addicks/Barker reservoir area"
   - "Flash Flood Warning" / "Rain outlook: Moderate"
   - "Brays Bayou at Gessner: Minor flooding"
4. Fine print (13px muted): "FloodReady summary, based on: FEMA flood map, City of Houston Harvey flood extent, NOAA/USGS gauges, OpenFEMA claims, NWS alerts and NOAA rain outlook. This is a summary rule, not a scientific risk score. [How we decide]". "How we decide" opens a Sheet that renders §4.3 verbatim in plain language.
5. Updated time (13px muted, `Clock` icon): "Updated 2:41 PM · Refresh" (Refresh is an icon button that re-runs all Home fetches).

**Loading:** the hero renders immediately with skeleton badges (2× 120×32), 3 skeleton chips (90×28) and the text "Checking your place…". Each signal fills in as its endpoint returns. A level is only final when `risk` has resolved (Right-now additionally needs `alerts` and `outlook`). A badge shows "Checking…" (Unknown style) until then. Do not flash "Lower".
**Partial data:** if an endpoint fails, its chip is replaced by a muted chip "Gauges unavailable", and the level is computed from the rest, with fine print "Some data is unavailable, so this summary may be incomplete." Exposure is **never "Lower" when `risk` itself failed**. It shows "Unknown" with "Try again".

### 4.3 Exact level rules (client-side, `src/lib/summary.ts`, pure and unit-testable)
Inputs come only from existing endpoints: `/risk`, `/flood-history`, `/zip-insurance` (when zip), `/alerts`, `/outlook`. `risk.nearest_gauges` provides current gauge status.

**A. Right now** (4 levels; reuses NWS stage names and mirrors `backend/app/services/watch.py`)
| Level | Fires when (first match wins, top down) | Reason line (en) |
|---|---|---|
| **Danger** | any alert `event` contains "Flash Flood Emergency", OR any nearest gauge `status === 'major'` | "{event} in effect" / "{gauge} is at major flood stage" |
| **Warning** | any flood alert (`/flood|hurricane|tropical|storm surge|coastal/i`) whose `event` contains "Warning", OR any gauge `moderate` or `minor` | "{event} in effect" / "{gauge} is at {minor/moderate} flood stage" |
| **Watch** | any other flood alert (Watch/Advisory/Statement), OR any gauge `action`, OR `outlook.day1.category` ∈ {Moderate, High} | "{event} in effect" / "{gauge} is near flood stage" / "{category} risk of excessive rain today" |
| **Normal** | none of the above | "No flood alerts or high water nearby." |
| **Unknown** | `alerts` AND `risk` both failed | "We can't check live conditions right now." |

Note: `outlook` Marginal/Slight do **not** raise the level; they appear as a chip only. This rule is a product choice; state it in "How we decide".

**B. This place: exposure** (3 levels; counts documented signals, no weights)
Strong signals (each one alone → **High exposure**):
- S1 `risk.sfha === true` (FEMA Special Flood Hazard Area, zones A*/V*). Source: FEMA NFHL / 12 CFR 339 link already used.
- S2 `risk.harvey.flooded === true`. Source: `risk.harvey.source`.

Supporting signals (any one → **Elevated exposure**; also shown as chips when High):
- E1 `risk.low_ground === true`
- E2 `risk.reservoir_area` is truthy (Addicks/Barker area)
- E3 any `flood-history.events[].nearest_gauge.peak_category` ∈ {moderate, major} **and** `distance_mi ≤ 3`. Chip copy must say "at nearest gauge", never "at your address" (reuse `c6.hist.note`).
- E4 `zip-insurance.claims.since_2017 ≥ 1` → **chip only, never raises the level by itself** (claims exist almost everywhere; we show the number, not a judgment).

Otherwise → **Lower exposure**. The reason line must read "Lower is not zero: floods can happen anywhere it rains hard." (reuses the sense of `home.noRiskToday`). If `risk.harvey.flooded === false`, add a chip "Not in Harvey's mapped extent" with the existing note "that does not mean it cannot flood".

Display labels (en / es): High exposure / Exposición alta · Elevated exposure / Exposición elevada · Lower exposure / Exposición menor · Unknown / Sin datos.

### 4.4 "Do these 3 things now"
A section title (20px/600) with a sub "Picked for Home based on your place and household." Below it are three **ActionCards**. Each card has a 40px icon tile, a title (17px/600), a one-line why (15px muted), a right `ChevronRight`, a whole-card link, and a trailing "Mark done" check button (44×44; done items move to a "Done (2)" disclosure at the bottom and the next rule fills the slot). Persist done state in `floodready.actionsDone.v1`; done items reappear after 90 days, except insurance, which reappears only when the place changes.

Candidate rules, evaluated in this priority order; take the first 3 that match and are not done:
| id | When | Title (en) | Why line (en) | Link |
|---|---|---|---|---|
| `drive` | Right now ≥ Watch | Check your route before you drive | Never drive through flooded roads. We'll flag flood-prone crossings on your way. | `#drive` |
| `alerts` | no push subscription for this place | Turn on flood alerts for {nickname} | Get a notification when alerts or nearby gauges rise. | `#alerts` |
| `medical` | household.medical.dialysis or oxygen or powerDevice | Line up backup {dialysis/oxygen/power} | See the nearest dialysis centers and what to pack. | `#prepare/medical` |
| `evac` | hasCar === false OR mobility ≠ none OR medical any | Register for help to evacuate | Texas STEAR registry and 2-1-1 can plan for people who need extra help. | `#prepare/evacuate` |
| `insurance` | exposure ∈ {High, Elevated} OR renter | Check when flood insurance would start | Most policies have a 30-day wait before coverage starts. | `#prepare/insurance` |
| `renter` | renter === true | Ask your landlord about past flooding | We'll draft the letter for you. | `#prepare/renters` |
| `plan` | no `lastPlan` in localStorage | Make your household plan | Takes about 2 minutes. | `#prepare/plan` |
| `ask` | always (filler) | Ask a flood question in your language | Answers cite their sources. | `#ask` |

Copy must not invent facts. "30-day wait" and STEAR/2-1-1 already exist in `home.c4` and `data/knowledge/special-needs-and-no-car.md`. Sub-route anchors (`#prepare/medical`) scroll to the section id on Prepare.

### 4.5 Live conditions
Section title "Live conditions" (Condiciones actuales) + "Updated {time}".
- **Alerts tile** (StatTile): label "NWS alerts". Value "None" (Normal style, 1 line) or the count + the top event name. When there are flood alerts, the tile expands to a list: each alert row has a RiskBadge (Warning/Watch by event), the event (16/600), the headline (15), "Expires {time}", and "Read" → Sheet with the description + the "weather.gov" SourceLink. Non-flood alerts sit under "Other weather alerts ({n})".
- **Rain outlook tile**: label "Excessive rain outlook today". Value = category (None / Marginal / Slight / Moderate / High), sub = API `label`, SourceLink "NOAA WPC".
- **Nearby gauges** list (Card): each row is 64px, a 3-column grid `[1fr auto 96px]`: name (15/500) + "{stage} ft · {distance} mi" (13 muted), a **StatusBadge** (gauge category with a plain label), and a 96×32 Sparkline with an aria-label "Water level, last 48 hours, rising/falling/steady". Under the list: "Gauge levels are for the stream, not your street." + "Show on map" (expands the existing Leaflet map, 240px, with a text-list fallback).
- **Gauge category plain labels** (replace raw NWS words everywhere): normal → "Normal", action → "Near flood stage", minor → "Minor flooding", moderate → "Moderate flooding", major → "Major flooding", unknown → "No data". es: Normal · Cerca del nivel de inundación · Inundación menor · Inundación moderada · Inundación mayor · Sin datos.

### 4.6 Home states
- **No place (skipped onboarding):** the hero is replaced by an EmptyState: icon `MapPinPlus` 40px, title "Set your place to see your flood summary", body "We'll check FEMA maps, Harvey flooding, nearby gauges and alerts for that address.", primary "Set my place" (opens the My place sheet), secondary link "Try a sample address" (fills "5300 N Braeswood Blvd, Houston, TX 77096", the demo address in `DEMO-DAY.md`). Below it, show Live conditions for Houston (the HOUSTON constant) titled "Houston right now".
- **Offline:** the hero shows the cached last result (the SW already caches risk) with a banner chip "Offline: showing results from {time}".
- **Error (risk failed):** an inline ErrorBox inside the hero: "We couldn't load the flood map data for this address." + "Try again".

---

## 5. Visual design system

### 5.1 Brand
- **Name lockup:** a shield mark (24px in header, 32px on Welcome) + wordmark "FloodReady" (17px/700, tracking -0.01em, `ink`) + "Houston" (17px/500, `muted`), with a 6px gap. In the sidebar the lockup is 2 lines on 240px if needed.
- **Mark (inline SVG, `src/components/brand/Logo.tsx`):** a rounded shield outline (stroke 2, `brand`) containing two horizontal wave lines (stroke 2, `water`), the lower one shorter. It replaces the drop icon in `public/icon.svg` and the maskable icons with the same motif on a `brand` square with a white shield. The motif reads as "protected from water".
- **Voice:** calm, direct, second person, short sentences, sentence case everywhere (no ALL CAPS chips). Numbers are digits. Verbs on buttons ("Save place", "Check route", "See when coverage starts").
- `theme-color` meta and manifest `theme_color`: `#0B4F94` (brand-strong); `background_color`: `#F4F6F9`.

### 5.2 Color tokens (contrast verified, WCAG 2.1)
Text tokens are ≥4.5:1 on `bg`, `surface` and `surface-2` and on their own tint. Ratios are listed against `surface`.

| Token | Light | Dark | Use | Light / Dark ratio |
|---|---|---|---|---|
| `bg` | #F4F6F9 | #0B1219 | page | — |
| `surface` | #FFFFFF | #131C26 | cards, header, bars | — |
| `surface-2` | #EDF1F5 | #1B2633 | inset rows, chips, skeleton base | — |
| `ink` | #0F1B2A | #E8EEF5 | primary text | 17.4 / 14.7 |
| `muted` | #4A5868 | #A3B1C2 | secondary text | 7.3 / 7.9 |
| `line` | #D7DEE6 | #2A3746 | dividers, card borders (decorative) | — |
| `ui` | #7A8796 | #6F8196 | input borders, control outlines (≥3:1) | 3.7 / 4.3 |
| `brand` | #0B5CAD | #6CB4F5 | links, primary buttons, active nav | 6.7 / 7.8 |
| `brand-strong` | #0B4F94 | #9ACBF8 | hover/pressed | — |
| `brand-ink` | #FFFFFF | #0B1219 | text on brand fill | 6.7 / 8.5 |
| `brand-tint` | #E6F0FA | #13304D | active nav bg, info callouts | — |
| `water` | #0E7C86 | #5CC8D0 | logo wave, sparklines, map route line | — |
| `normal` / `normal-tint` | #1B6E3C / #E7F4EC | #5FD08A / #12301F | Normal, Lower exposure, "Looks safe" | 6.3 / 8.9 |
| `watch` / `watch-tint` | #875D00 / #FDF3D6 | #F2C94C / #33290B | Watch, Near flood stage, Elevated | 5.8 / 10.8 |
| `warning` / `warning-tint` | #B04A06 / #FDEDE2 | #FF9F5A / #3A2214 | Warning, Minor/Moderate flooding, Caution | 5.5 / 8.5 |
| `danger` / `danger-tint` | #B42318 / #FCEBEA | #FF8A80 / #3B1A19 | Danger, Major flooding, High exposure, Avoid | 6.6 / 7.5 |
| `strip-bg` / `strip-ink` | #0F1B2A / #FFFFFF | #E8EEF5 / #0B1219 | 911 strip (inverse) | 17.4 / 16.1 |

**Semantic mapping (one table, used everywhere; `src/lib/levels.ts`)**
| Concept | normal | watch | warning | danger |
|---|---|---|---|---|
| Right now | Normal | Watch | Warning | Danger |
| Exposure | Lower | Elevated | — | High |
| Gauge | normal | action | minor, moderate | major |
| Route verdict | safe "Looks clear" | — | caution "Use caution" | avoid "Avoid this route" |
| Watch level (API) | ok | watch | warning | — |
| Icon (lucide) | `CircleCheck` | `Eye` | `TriangleAlert` | `OctagonAlert` |

Never use color alone: every badge has its icon and its text label. `unknown` uses `muted` on `surface-2` with `CircleHelp`.

### 5.3 Typography
Font: **Inter Variable** self-hosted via `@fontsource-variable/inter` (so it is cached by the SW and works offline), with fallback `system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif`. For zh/ar, the system stack takes over automatically (Inter lacks those glyphs). Use `font-feature-settings: "cv11", "ss01"` and `tabular-nums` on all numbers.

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `display` | 30/36 (mobile) · 36/44 (≥768) | 700 | Hero level text inside RiskBadge lg, verdict |
| `h1` | 24/32 | 700 | Page title |
| `h2` | 20/28 | 600 | Section title |
| `h3` | 17/24 | 600 | Card title, action title |
| `body` | 16/24 | 400 | Default (never below 16 for inputs, to avoid iOS zoom) |
| `body-sm` | 15/22 | 400 | Secondary lines |
| `caption` | 13/18 | 500 | Meta, source lines, fine print (minimum size anywhere) |
| `overline` | 12/16, uppercase, +0.06em | 600 | Eyebrows, sidebar group labels |

### 5.4 Spacing, radius, elevation, motion
- 4px base. Page gutter 16 (mobile) / 24 (desktop). Section gap 24 (32 desktop). Card padding 16 (20 for hero/primary). Gap inside cards 12. Chip gap 8.
- Radius: `sm` 8 (inputs, chips-square), `md` 12 (buttons, tiles), `lg` 16 (cards), `xl` 20 (hero, sheets top corners), `full` (pills, badges).
- Elevation (light): `shadow-card` = `0 1px 2px rgb(15 27 42 / .06), 0 1px 3px rgb(15 27 42 / .04)`; `shadow-raised` = `0 8px 24px rgb(15 27 42 / .14)` (sheets, toasts). Dark: no shadows on cards (use `line` borders); sheets use `0 8px 24px rgb(0 0 0 / .5)`.
- Cards: `bg-surface border border-line rounded-lg shadow-card`. Remove the double borders used today.
- Motion: 150ms ease-out for hover/press, 200ms for sheets (translate-y 16px + fade), 300ms for skeleton→content fade. The existing `prefers-reduced-motion` rule stays. Never animate the RiskBadge color.
- Focus: keep the `:focus-visible` 3px brand outline at 2px offset.

### 5.5 Tailwind v4 tokens (replace the token block in `src/index.css`)
```css
@import "tailwindcss";
@import "@fontsource-variable/inter";
@import "leaflet/dist/leaflet.css";
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));

:root {
  --bg:#F4F6F9; --surface:#FFFFFF; --surface-2:#EDF1F5; --ink:#0F1B2A; --muted:#4A5868; --line:#D7DEE6; --ui:#7A8796;
  --brand:#0B5CAD; --brand-strong:#0B4F94; --brand-ink:#FFFFFF; --brand-tint:#E6F0FA; --water:#0E7C86;
  --normal:#1B6E3C; --normal-tint:#E7F4EC; --watch:#875D00; --watch-tint:#FDF3D6;
  --warning:#B04A06; --warning-tint:#FDEDE2; --danger:#B42318; --danger-tint:#FCEBEA;
  --strip-bg:#0F1B2A; --strip-ink:#FFFFFF;
  --c-line:var(--water); --c-grid:#E3E8EE;
  /* legacy aliases so un-migrated components keep working until P6 */
  --s-normal:var(--normal); --s-action:var(--watch); --s-minor:var(--warning); --s-moderate:var(--warning);
  --s-major:var(--danger); --s-unknown:var(--muted);
}
:root[data-theme="dark"] {
  --bg:#0B1219; --surface:#131C26; --surface-2:#1B2633; --ink:#E8EEF5; --muted:#A3B1C2; --line:#2A3746; --ui:#6F8196;
  --brand:#6CB4F5; --brand-strong:#9ACBF8; --brand-ink:#0B1219; --brand-tint:#13304D; --water:#5CC8D0;
  --normal:#5FD08A; --normal-tint:#12301F; --watch:#F2C94C; --watch-tint:#33290B;
  --warning:#FF9F5A; --warning-tint:#3A2214; --danger:#FF8A80; --danger-tint:#3B1A19;
  --strip-bg:#E8EEF5; --strip-ink:#0B1219; --c-grid:#26323F;
}
@theme inline {
  --font-sans: "Inter Variable", system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif;
  --color-bg:var(--bg); --color-surface:var(--surface); --color-surface-2:var(--surface-2); --color-ink:var(--ink);
  --color-muted:var(--muted); --color-line:var(--line); --color-ui:var(--ui);
  --color-brand:var(--brand); --color-brand-strong:var(--brand-strong); --color-brandink:var(--brand-ink); --color-brand-tint:var(--brand-tint);
  --color-water:var(--water);
  --color-normal:var(--normal); --color-normal-tint:var(--normal-tint); --color-watch:var(--watch); --color-watch-tint:var(--watch-tint);
  --color-warning:var(--warning); --color-warning-tint:var(--warning-tint); --color-danger:var(--danger); --color-danger-tint:var(--danger-tint);
  --color-strip:var(--strip-bg); --color-stripink:var(--strip-ink);
  --radius-sm:8px; --radius-md:12px; --radius-lg:16px; --radius-xl:20px;
  --shadow-card:0 1px 2px rgb(15 27 42 / .06), 0 1px 3px rgb(15 27 42 / .04);
  --shadow-raised:0 8px 24px rgb(15 27 42 / .14);
  --text-display:30px; --text-display--line-height:36px;
}
```
Note: `--s-moderate` now maps to `warning`, not red. Moderate gauge flooding is shown orange with the text "Moderate flooding". Red is reserved for Major, Danger and Avoid.

### 5.6 Icons
Add `lucide-react` (pin an exact version from npm at install time). Default size 20, stroke 2, `aria-hidden`, with the accessible name on the parent. Mapping: Home `House`, Alerts `BellRing`, Drive `Route`, Prepare `ShieldCheck`, Ask `MessageCircleQuestion`, Replay `History`, After a flood `LifeBuoy`, Civic `Landmark`, Settings `Settings`, About `BookOpen`, Place `MapPin`, Phone `Phone`, Speak `Volume2`, Stop `Square`, Mic `Mic`, Source `ExternalLink`, Calendar `CalendarPlus`, Report `Megaphone`, Swap `ArrowUpDown`, Locate `LocateFixed`, Info `Info`, Close `X`, Done `Check`, Menu `Menu`, Language `Languages`, Install `Download`, Theme `Sun`/`Moon`, Refresh `RefreshCw`, Gauge `Waves`, Rain `CloudRain`, Insurance `FileText`, Medical `HeartPulse`, Car `Car`, Evac `Accessibility`. **No emoji anywhere in UI chrome**, including button labels and map tooltips (`⚠`, `👥` → lucide or text).

### 5.7 Components (`src/components/ds/*.tsx`, one file each; re-export from `src/components/ds/index.ts`)
| Component | Props | Spec |
|---|---|---|
| `Card` | `title?, subtitle?, action?, tone?: 'default'\|'inset'\|level, padding?: 'md'\|'lg', as?` | Spec in §5.4. Title h3; `action` slot top-right (link or icon button). `tone=level` adds a 4px top border in the level color. |
| `StatTile` | `label, value, sub?, icon?, level?, source?` | Min-h 88, padding 16, radius md, `bg-surface-2`. Label is overline; value is 22/28 600 tabular. |
| `RiskBadge` | `level: 'normal'\|'watch'\|'warning'\|'danger'\|'unknown', label, size: 'sm'\|'md'\|'lg'` | Pill. Bg = tint, text and icon = level color, 1px border level color at 40% opacity. sm 24px/13px, md 32px/15px, lg 44px/20px 700. Icon from §5.2. |
| `StatusBadge` | `status: Status` | Wraps RiskBadge sm with the gauge plain labels from §4.5. Replaces `StatusChip`. |
| `SourceLink` | `href, label?` | Inline-flex, 13px/500, brand, underline offset 2, `ExternalLink` 12px, preceded by a space. Friendly label map by host: `geogimsms.houstontx.gov`→"City of Houston", `hazards.fema.gov`→"FEMA", `api.weather.gov`/`weather.gov`→"National Weather Service", `wpc.ncep.noaa.gov`→"NOAA WPC", `fema.gov` OpenFEMA→"OpenFEMA", `waterdata.usgs.gov`→"USGS", `water.noaa.gov`→"NOAA", `hcfcd.org`→"HCFCD", `communityimpact.com`→"Community Impact", `reduceflooding.com`→"ReduceFlooding.com", fallback hostname. Opens in a new tab with `rel="noreferrer"` and an sr-only "(opens in new tab)". Replaces `SrcLink`. |
| `EmptyState` | `icon, title, body?, action?, secondary?` | Centered, padding 32/16, icon 40 in a 64px `surface-2` circle, title h3, body 15 muted max 40ch. |
| `Skeleton` | `w, h, radius?` / `SkeletonText lines` | `bg-surface-2`, shimmer gradient 1.2s (disabled by reduced motion). `aria-hidden`. The parent carries `aria-busy="true"` and an sr-only "Loading". |
| `Toast` + `useToast()` | `message, action?, tone?` | Bottom-center above the tab bar (bottom = 80 + safe area), max-w 420, radius md, `bg-ink text-surface`, shadow raised, auto-dismiss 5s (errors stay until dismissed), `role="status"`. Replaces the inline SW update toast in `main.tsx` ("A new version is ready." + "Reload"). |
| `Sheet` | `open, onClose, title, side: 'bottom'\|'right', children` | Mobile = bottom sheet, max-h 85vh, radius xl top, a grab handle 36×4. Desktop = right drawer 420px. Native `<dialog>` with `showModal()` for focus trap and Esc; backdrop `rgb(15 27 42 / .45)`. Title h2 + close button `X` 44×44. |
| `Stepper` | `steps: string[], current` | "Step 2 of 3" text + 3 segment bars (4px, gap 4, brand / line). Used in onboarding and the plan builder. |
| `Tabs` | `items, value, onChange` | Underline tabs, 44px tall, `role="tablist"`, arrow-key nav. Used on Prepare (sections) and Civic. |
| `Segmented` | `options, value, onChange, size` | `surface-2` track, radius md, selected = surface + shadow-card. 44px tall. `role="radiogroup"`. Used for Type/Talk, I rent/I own, Standard/Live, storm picker on mobile. |
| `Disclosure` | `title, preview?, defaultOpen?, id` | 56px row button with `aria-expanded`, `ChevronDown` rotating 180° (150ms); content in a region. Opens automatically when `location.hash` targets its `id`. |
| `ActionCard` | `icon, title, why, href, onDone` | See §4.4. |
| `Button` | `variant: 'primary'\|'secondary'\|'ghost'\|'danger', size: 'md'\|'lg', icon?, loading?` | md 44px / lg 52px, radius md, 16px/600. Primary = brand fill; secondary = surface + `ui` border; ghost = text brand; danger only for "Call 911". `loading` shows a 16px spinner and keeps the width. Replaces `Btn`. |
| `Field`, `Input`, `Select`, `Checkbox` | as today | Inputs 48px, radius sm, border `ui`, focus ring brand. Checkbox 24px with a 44px label hit area. |

### 5.8 911 strip (`EmergencyStrip.tsx`)
- Always present, 36px, `bg-strip text-stripink`, centered on mobile, left-aligned on desktop (over the content column). Content: `Phone` 16px + "In danger? **Call 911**" (link `tel:911`, the whole strip is the hit target, 44px min via padding) + on ≥768px, after a separator: "Not official guidance" (muted at 80% opacity).
- **Escalation:** when Right-now = Danger, the strip becomes `bg-danger text-white` with "{NWS event} for {nickname}. If you are trapped by water, call 911." (`role="alert"`, announced once). Calm the rest of the time.
- Remove the separate footer disclaimer line (it moves into the strip on desktop, and into About + the Home trust card on mobile).

---

## 6. Per-screen specs

Common page template: `PageHeader` (h1 + optional 15px subtitle + optional right action), 24px gap, then sections. Every page uses My place by default and shows a 13px "For: Home · 5300 N Braeswood Blvd · Change" line when the content depends on the place (Change opens the My place sheet).

Common states:
- **Loading:** skeletons shaped like the content (never a bare "Loading…").
- **Empty:** EmptyState with one action.
- **Error:** inline ErrorBox: `danger-tint` bg, `danger` 1px border, `TriangleAlert` icon, plain message + "Try again". Never a raw HTTP error. The existing `offline` string stays as the generic fallback.
- **Offline:** a global top banner below the 911 strip: `surface-2`, `WifiOff` icon, "You're offline. Your saved place, plan and safety steps still work." (es: "Sin conexión. Su lugar guardado, su plan y los pasos de seguridad siguen disponibles.") Feature-specific lines are listed per screen below.

### 6.1 Drive (`#drive`)
Order:
1. PageHeader: "Check a route" (es: "Revise una ruta"); subtitle "We check your route against flood-prone crossings, live alerts, gauges and recent road reports."
2. **Safety banner** (always, above the form): Card tone `watch-tint`, `Car` icon, 17px/600 "Never drive through flooded roads." + 15px "Water over a road can be deeper and faster than it looks. Turn around." No statistics here: the repo has no sourced "depth that floats a car" fact. Also, `flood-problems.md` A3 notes that the generic slogan alone shows "no convincing evidence" of saving lives, so the personal verdict below is the real message, and the banner stays one short line.
3. **Route form card:** "From" is prefilled with My place (shows nickname chip "Home" inside the input with an `X` to clear) and has a `LocateFixed` "Use my location" icon button (Geolocation API → coords directly, label "Current location"). "To" is empty with placeholder "Where are you going?". A `ArrowUpDown` swap button sits between the fields (44×44, aria-label "Swap From and To"). Under "To": up to 3 chips of Watched places (from Alerts) as quick destinations. Primary button lg full width: "Check route" (es: "Revisar ruta").
4. **Verdict card** (after the result, scroll into view, focus moves to the heading): Card tone = verdict level. RiskBadge lg ("Looks clear" / "Use caution" / "Avoid this route"), then the API `message` (17px), then the "Hazards on this route" list: each row has a `TriangleAlert` (or `Megaphone` for community reports with a "Community report" tag), name (16/600), reason (15), and a SourceLink when present. Actions: "Read aloud" (`Volume2`) and "Report water on a road" (opens ReportSheet). Never show "Looks clear" when routing failed (existing backend rule); the copy for that case is "We couldn't check this route. Treat low roads and underpasses as unsafe in heavy rain."
5. **Map** (h 320 mobile / 440 desktop): the route line in `water` 5px, hazards as danger markers with a white 2px ring, crossings as small warning (high) / watch (medium) dots. Legend row under the map: "● Flood-prone crossing (high) ● Flood-prone crossing (medium) ▲ Hazard on your route". Disclosure under it: "List of {n} flood-prone crossings" (existing text list).
- States: loading = verdict skeleton (badge + 2 lines) + map with a spinner overlay; geocode error = "We couldn't find '{text}'. Add a ZIP code."; offline = "Route checks need a connection. Your last checked route is shown below." (cached).
- **Demo mode only:** a "Sample routes" chip row above the form (the existing `/route-check/demo`) and a "Simulate storm" switch, both inside a dashed-border `DemoPanel` (§7).

### 6.2 Alerts (`#alerts`)
Order:
1. PageHeader "Flood alerts" (es: "Alertas de inundación"); subtitle "We watch NWS alerts, river gauges, flood-prone crossings and road reports near your places."
2. **"Alerts on this phone" card:** Switch row (52px): `BellRing` + "Alerts on this phone" + sub "Get a notification when conditions get worse at your places, even when the app is closed." + Switch. States: Off / On ("On for 2 places") / Blocked ("Notifications are blocked in your browser settings.") / Unsupported ("This browser can't receive alerts. You'll still see changes while the app is open."). iOS not standalone: an inline info box "On iPhone: tap Share → Add to Home Screen, then open FloodReady from your Home Screen to turn on alerts." This one switch replaces PushCard's 3 buttons and Watch's "Enable notifications". Implementation: subscribe to push; if push is unsupported, request `Notification` permission for in-app polling.
3. **Places list:** My place is always first (badge "My place", cannot be removed here, only changed). Each place card (Card tone = level) shows the nickname (17/600) + address (13 muted) + RiskBadge md (Normal / Watch / Warning, mapped from `ok|watch|warning`); the `message`; "Why" bullets (`reasons`); a "{n} crossings nearby · {m} alerts" meta line; gauge StatusBadges; actions "Read aloud", "Check a route here" (`#drive` with To prefilled), and an overflow `MoreHorizontal` → "Remove".
4. "Add a place" button (secondary, `Plus`) → Sheet with Name Segmented (Home/Family/Work/School/Other) + Address → "Watch this place".
5. "Report flooding" row (`Megaphone`) → ReportSheet.
- Polling: keep the 2-minute poll while open; show "Checked {time}" + a refresh icon button in the header action slot. Spoken announcement on rise stays (existing), plus a Toast.
- Empty: impossible once My place exists. Without My place, show the EmptyState "Set your place to get alerts" → My place sheet.
- **Demo mode only:** DemoPanel with "Send test alert", "Simulate storm alert" (push simulate) and a "Simulate storm (in-app)" switch.

### 6.3 Storm replay (`#replay`)
Order:
1. PageHeader "Storm replay" (es: "Repetición de tormentas"); subtitle "See how real storms rose at the gauges near your place, using USGS gauge records."
2. **Storm picker:** 4 cards in a horizontal snap-scroll (mobile) / 4-column grid (desktop). Card 160×88: storm name (16/600) + dates (13 muted) + the selected state (brand border 2px + `Check`). The order comes from `/replay/events`.
3. **Fact card** for the selected event: `summary` text, with key numbers bolded (wrap digits in `<b>` by regex, with no new numbers) + SourceLink.
4. **Player (sticky under the header on mobile when scrolled past):** Play/Pause button lg (`Play`/`Pause`), timeline slider (full width, 44px hit area) with the date-time label (localized `toLocaleString(lang)`), a "Narrate" toggle (`Volume2`), and a speed Segmented 1× / 4×.
5. **Map** with a legend: gauge dots colored by current category (StatusBadge colors), My place as a brand square marker labeled "Your place", and the selected gauge with a ring. Under the map is a text list of gauges and their current categories (a11y equivalent).
6. **Gauge detail**: a select of gauges (default = nearest to My place) + WaterTube + StageChart side by side on desktop.
7. "Shift the storm" card (existing) moves into a Disclosure "What if the storm had shifted a few miles?".
- States: loading = picker skeleton (4 cards) + map placeholder; `replay.noData` → EmptyState "No gauge records for this storm."

### 6.4 Prepare (`#prepare`)
Use `Tabs` at the top (sticky): **Plan · Insurance · Medical · Renters · Evacuation help**. The default tab is chosen by household: dialysis → Medical; renter → Renters; else Plan. Hash anchors `#prepare/plan|insurance|medical|renters|evacuate` select the tab.

- **Plan:** a summary of the household (chips) + "Edit household" (Sheet). Primary "Build my plan" / after it exists: "Update my plan". The plan renders as a 4-step timeline (Now · When a storm is forecast · During the storm · After), each a Card with checkable steps (persisted). Footer: "Built from your household answers. Not official guidance." (Drop "Plan by: template/gemini"; in demo mode show it as a caption.) Loading: Stepper-like skeleton "Building your plan…".
- **Insurance:** h2 "When would flood insurance start?" Field "If I buy a policy on" (date, default today). Button "See when coverage starts" (es: "Ver cuándo empieza la cobertura"). Result: StatTile "Coverage starts" = `effective_date` (formatted "Thursday, Nov 12") + the API `message` + "Add reminder to calendar" (`CalendarPlus`, existing .ics) + SourceLink. Below: the link row "See flood claims and premiums for ZIP {zip}" → Home disclosure `#home/rentbuy`.
- **Medical:** MedicalAccess (it uses My place; there is no free-text dependency now; it runs when household.medical.dialysis or the user taps "Find dialysis centers near {nickname}"). Each facility row: name, distance, address, and a "Call" button (`Phone`, `tel:`).
- **Renters:** TenantLetter (existing) + the `home.c5` line + SourceLink.
- **Evacuation help (new, content from `data/knowledge/special-needs-and-no-car.md`, sources tdem.texas.gov/stear, 211texas.org, readyharris.org):** h2 "If you need help to evacuate". 3 rows: "Register with STEAR (free, voluntary)" + 1-line description + buttons "Register online" (stear.texas.gov) and "Call 2-1-1"; "Call 2-1-1 before the storm" + "Ask about evacuation transportation and shelters."; "Call 311 for city services, 911 for danger to life." The copy must be shortened from the knowledge card, not invented. es parity required.
- **Official alert systems** (formerly "Get alerts (one tap)"), at the bottom of the Plan tab: the 2 existing external links, as list rows with `ExternalLink`.

### 6.5 After a flood (`#recover`)
Order (re-sequenced for the moment of need):
1. PageHeader "After a flood" (es: "Después de una inundación"); subtitle "Steps to stay safe, document damage and get help."
2. **Share911** card (existing) at top: "Share your location with 911 or family".
3. **Safety first**: the existing checklists (post-flood safety, money safety, mold) as Disclosures, with progress "3 of 7 done".
4. **RecoveryTracker** (existing) as "Your recovery checklist".
5. **FEMA aid steps** (existing content).
6. "Report flooding" row → ReportSheet; a "Recent reports near {nickname}" mini-list (latest 5) + "Show map" disclosure.
7. **Historical shelters**, collapsed Disclosure: title "Shelters used during Harvey (2017)", preview "Historical list, not current". When open: the existing warning box first (now `watch-tint`, `Info` icon), then the list, distances from **My place**. Never in the first screen.
- Empty for reports: "No community reports near {nickname} in the last day."

### 6.6 Who's responsible (`#civic`)
Order: PageHeader "Who's responsible" (es: "Quién es responsable"); subtitle "Find out who handles drainage, reservoirs and flood projects where you live." Then **WhoToContact** + officials first (the most actionable), then "Flood bond projects near {nickname}" (existing bond facts + projects with status chips), then "Addicks and Barker reservoirs" (existing reservoir card, the in-area result as a RiskBadge-style chip). Each section is a Card with SourceLinks. Loading = 3 card skeletons.

### 6.7 Ask (`#ask`)
Layout: PageHeader "Ask FloodReady" (es: "Pregunte a FloodReady") + right action `Settings2` icon → the Voice settings sheet. Subtitle (13 muted): "Answers use FloodReady's sourced guides and your place. Not official guidance. In an emergency, call 911."

**Mode Segmented** at top: **Type** (`Keyboard`) · **Talk** (`Mic`). Default Type; remember the choice in localStorage.

**Type mode:**
- Empty state (no messages): an EmptyState with `MessageCircleQuestion`, title "What do you want to know?", then **suggested question chips** (wrap, 44px tall, `surface-2`, radius full, 15px). Pick 4, personalized: medical first if dialysis, renter first if renter, otherwise the base order. Tapping a chip sends it immediately.

| id | en | es |
|---|---|---|
| street | What do I do if my street floods? | ¿Qué hago si mi calle se inunda? |
| zone | Is my address in a flood zone? | ¿Mi dirección está en zona de inundación? |
| renters | Does renters insurance cover floods? | ¿El seguro de inquilino cubre inundaciones? |
| start | If I buy flood insurance today, when does it start? | Si compro seguro contra inundaciones hoy, ¿cuándo empieza? |
| dialysis | Where is the nearest dialysis center? | ¿Dónde está el centro de diálisis más cercano? |
| nocar | How do I evacuate without a car? | ¿Cómo evacúo si no tengo carro? |
| drain | Who do I call about a clogged storm drain? | ¿A quién llamo por un desagüe tapado? |

- Messages: user bubbles right (`brand` fill, max 85%), assistant left (`surface`, border `line`). Assistant answer markdown (existing `Md`), then an actions row: "Listen" (`Volume2`), "Copy" (`Copy`). Then **Sources** as a compact list of SourceLink with friendly labels (max 3 visible + "{n} more"). Then a Disclosure "How this answer was made" (13px muted) containing `generated_by` in plain words ("Written by Gemini from FloodReady's guides" / "Built from FloodReady's guides (no AI)") and the tools used in plain words (get_risk → "your flood risk", get_alerts → "live alerts", check_route → "route check", search_knowledge → "FloodReady guides", insurance_countdown → "insurance timing", get_civic → "local responsibility", flood history → "flood history", zip claims → "ZIP claims", dialysis → "dialysis centers").
- Thinking state: an assistant bubble with a 3-dot typing indicator + "Checking sources…".
- Composer: sticky above the tab bar; Input (48px, placeholder "Ask about flood risk, insurance, safety…") + a dictation `Mic` icon button (44, aria-label "Speak your question") + Send (`SendHorizontal`, primary, 44). The 500-char limit shows a counter only after 400.
- Error bubble: "I couldn't answer that right now. Try again, or check the sources on Home." + Retry. 429: "Too many questions in a minute. Please wait a moment and try again."

**Talk mode (voice UI):**
- A centered **orb**: 168px circle (144px on <360px wide), positioned in the upper-middle of the free space. The state is shown by color, motion and a text label under it (17px/600) + a hint (15 muted). The whole orb is the button (`aria-pressed`, aria-label = the state label + hint).

| State | Orb visual | Label (en / es) | Hint (en) |
|---|---|---|---|
| idle | `brand` fill, `Mic` 48px white | Tap to talk / Toque para hablar | Ask in English or Spanish. Tap again to stop. |
| listening | `brand` fill + a 3-ring ripple (scale 1→1.35, 1.6s loop) driven by the input level when available | Listening… / Escuchando… | Live transcript shows below in quotes |
| thinking | `brand-strong` fill + a rotating conic arc (1.2s) | Thinking… / Pensando… | Checking sources |
| speaking | `water` fill + an equalizer of 5 bars | Speaking… tap to interrupt / Hablando… toque para interrumpir | — |
| paused | `surface-2` fill, `ui` border, `Mic` in brand | Paused, tap to continue / En pausa, toque para continuar | — |
| error / unsupported | `surface-2`, `MicOff` in muted | Voice isn't available here / La voz no está disponible aquí | "Try Chrome or Safari, or switch to Type." + button "Switch to Type" |

Never red for listening. Reduced motion: no ripple or rotation; use an opacity pulse only on the label dot.
- Under the orb: the live transcript (the user's interim text, 17px, in quotes) and the last answer as a normal assistant bubble with Sources (so voice users still get citations). "End conversation" ghost button at the bottom.
- Live engines (`LiveTalk`, `ElAgentTalk`) render **inside the same orb shell**: map their states to the table above. Their internal debug text moves to the demo-only diagnostics.
- **Voice settings sheet** (header action and Settings): Segmented "Voice": **Standard** (es: Estándar), "Reliable, works everywhere" · **Live (beta)** (es: En vivo, beta), "Faster back-and-forth conversation. May not work on every network." Mapping: Standard = engine `fast`; Live = engine `live`. **ElevenLabs Agent** appears as a third option "Agent (beta)" only in demo mode. Also a "Speak answers aloud in Type mode" switch (default off).
- **Hidden in production:** Latency details, "first audio … ms", `server` ms, filler markers. They move into the DemoPanel "Diagnostics" (demo mode).

### 6.8 Judge (`#judge`, demo mode)
Reached via `?demo=1` (§7) or a long-press on the logo for 2s (an undocumented escape hatch). Layout (desktop optimized for a projector; mobile works):
1. PageHeader "Judge demo"; subtitle "Two minutes, five steps. Every fact links to its public source."
2. Left column: QR card (existing; QR 224px on white, the URL under it) + "Demo mode is on" switch + "Reset demo" button (clears place/household/actionsDone and sets the demo place).
3. Right column: **Guided script**, 5 numbered StepCards. Each has a title, one line of what to look at, a "Go" button that sets state and navigates, and a checkbox:
   1. "Risk in one screen": Go = set My place to "5300 N Braeswood Blvd, Houston, TX 77096" (geocode), household = {renter: false, hasCar: true}, → `#home`. Look for: "High exposure: flooded in Harvey, Zone AE, ZIP claims chip."
   2. "Avoid a flooded underpass": Go = `#drive` with the sample route "Downtown: Allen Parkway underpass" preloaded and Simulate storm on, auto-run. Look for: "Avoid this route" with named crossings.
   3. "Replay Harvey": Go = `#replay` with Harvey selected and Narrate on. Look for: gauges crossing flood stages.
   4. "Ask in Spanish": Go = switch lang to es, `#ask` in Talk mode, prefill the chip "¿Qué hago si mi calle se inunda?". Look for: sourced steps + 911.
   5. "Push alert": Go = `#alerts` with the DemoPanel open. Look for: "Simulate storm alert" → notification on the phone.
4. Footer: "Limitations we say up front" (bullet list copied from DEMO-DAY.md "Say before they ask").

---

## 7. Demo mode
- **Turn on:** URL `?demo=1` (read once on load in `PlaceProvider`, store `floodready.demo=1` in **sessionStorage**, then `history.replaceState` to remove the param), the Judge page switch, or the logo long-press.
- **Turn off:** `?demo=0`, the badge's "Exit", or closing the tab (session-scoped).
- **Badge:** in the header, before the language button: a pill `bg-watch-tint text-watch`, border `watch`, `FlaskConical` 14px + "Demo mode" (es: "Modo demo") + a `X` button (aria-label "Exit demo mode"). On mobile it shows the icon + "Demo" only. Also add a fixed 2px `watch` line at the very top of the viewport so screenshots show demo mode.
- **`DemoPanel` component:** a dashed 1.5px `watch` border, `watch-tint` bg, radius lg, overline "Demo controls: not shown to residents". It renders `null` unless `demo`.
- **Inventory: what moves behind demo:**
| Control | File | Where it shows in demo |
|---|---|---|
| Demo routes chips | `Drive.tsx` | DemoPanel above the route form, renamed "Sample routes" |
| Simulate storm checkbox (route) | `Drive.tsx` | DemoPanel switch |
| Simulate storm (demo) checkbox, Refresh | `Watch.tsx` | DemoPanel on Alerts |
| Send test alert, Simulate storm push | `PushCard.tsx` | DemoPanel on Alerts |
| Latency details | `Ask.tsx` | DemoPanel "Diagnostics" on Ask |
| ElevenLabs Agent engine | `Ask.tsx` | Voice settings 3rd option |
| "via {generated_by}", "Tools:", "Plan by:" | `Ask.tsx`, `Prepare.tsx` | Plain-language disclosure for everyone; raw values as a caption in demo |
| Judge nav item | `App.tsx` | More menu + sidebar |
- Any simulated result must carry a visible "Simulated" tag (RiskBadge suffix " · Simulated") so a screenshot can never pass as real.

---

## 8. Implementation plan

Rules: each phase ≤2h for one builder agent. Phases in the same wave touch disjoint files and can run in parallel. **i18n:** each phase adds its strings to its **own new dictionary file** `src/i18n/p{N}.ts` (exporting `en` and `es`), merged in `src/i18n.ts`. This is the only shared edit, a one-line import + spread, done by P1 for all phases up front (P1 creates empty `p2.ts`…`p6.ts` stubs so later phases never edit `i18n.ts`). Run `npm run build` and `npm run lint` before handing back.

### Wave 1 (alone; everything depends on it)
**P1: design system, shell/nav, onboarding, My place context** (2h)
- Add deps: `lucide-react`, `@fontsource-variable/inter` (exact versions; report them).
- Edit: `src/index.css` (tokens §5.5), `src/App.tsx` (new nav §3.1–3.7, hash aliases, EmergencyStrip, header, More sheet, offline banner, onboarding gate), `src/ctx.tsx` (re-export from the new provider), `src/main.tsx` (Toast for SW update), `src/i18n.ts` (merge `p1`…`p6`), `index.html` + `public/manifest.webmanifest` (theme colors), `public/icon.svg` (+ regenerate the PNG icons only if a script exists; otherwise leave the PNGs and note it).
- Create: `src/components/ds/{Card,StatTile,RiskBadge,StatusBadge,SourceLink,EmptyState,Skeleton,Toast,Sheet,Stepper,Tabs,Segmented,Disclosure,ActionCard,Button,Field,DemoPanel,index}.tsx`, `src/components/brand/Logo.tsx`, `src/components/shell/{EmergencyStrip,Header,BottomNav,Sidebar,MyPlaceSheet,MoreSheet,LanguageSheet}.tsx`, `src/state/place.tsx` (§3.4, including `demo`), `src/lib/levels.ts` (§5.2 mapping), `src/pages/Welcome.tsx` (§3.5), `src/pages/Settings.tsx`, `src/pages/About.tsx`, `src/i18n/p1.ts` … `p6.ts`.
- Keep `components/ui.tsx` exports working: re-implement `Card`, `Btn`, `SrcLink`, `StatusChip`, `ErrorBox`, `Loading` as thin wrappers over `ds/*`, so un-migrated pages instantly inherit the new look.
- Done when: a fresh load shows Welcome; after finishing, the header chip shows the place on every tab across reloads; 5 tabs on mobile; `?demo=1` shows the badge.

### Wave 2 (parallel, after P1)
**P2: Home** (2h). Own: `src/pages/Home.tsx`, `src/lib/summary.ts` (+ `src/lib/summary.test.ts` if vitest is already present; otherwise a pure-function self-check is not required), `src/components/home/{SummaryHero,WhyChips,TopActions,LiveConditions,PlaceProfile}.tsx`. Move, but do not rewrite internally, `src/components/RentBuy.tsx` (restyle only), `src/components/Sparkline.tsx` (size props + aria-label), `src/i18n/p2.ts`.

**P3: Drive + Alerts** (2h). Own: `src/pages/Drive.tsx`, `src/pages/Watch.tsx` (rename the display to Alerts; the file name can stay), `src/components/PushCard.tsx` → `AlertsSwitch.tsx`, `src/components/ReportSheet.tsx` (extracted from Recover's form; P5 imports it), `src/components/maps.tsx` (legend slot, theme colors), `src/i18n/p3.ts`.

**P4: Ask + voice UI** (2h). Own: `src/pages/Ask.tsx`, `src/components/ask/{SuggestedQuestions,VoiceOrb,MessageList,Composer,VoiceSettingsSheet}.tsx`, `src/components/LiveTalk.tsx`, `src/components/ElAgentTalk.tsx` (state mapping only), `src/i18n/p4.ts`. Do not touch `speak.ts` or `audio/live.ts` logic.

**P5: Prepare + Recover + Civic + Replay + Judge** (2h; split into P5a Prepare+Judge and P5b Recover+Civic+Replay if two agents are free). Own: `src/pages/Prepare.tsx`, `src/components/{MedicalAccess,TenantLetter}.tsx` (restyle), new `src/components/prepare/EvacuationHelp.tsx`, `src/pages/Recover.tsx`, new `src/pages/Civic.tsx` (moves civic sections out of Recover), `src/components/{RecoverExtras,WhoToContact}.tsx` (restyle), `src/pages/Replay.tsx`, `src/components/{StageChart,WaterTube}.tsx` (token colors), `src/pages/Judge.tsx`, `src/i18n/p5.ts`. P5 imports `ReportSheet` from P3. If P3 isn't merged yet, P5 links "Report flooding" to `#alerts` and P6 swaps it.

### Wave 3
**P6: polish** (2h). Own: any file, after waves 1–2 merge, in this order:
1. Motion: sheet/disclosure/skeleton transitions per §5.4; reduced-motion check.
2. Empty, error and offline states: walk every screen with the network off and every endpoint 500ing (DevTools request blocking) and fix any gaps against §6.
3. Copy QA: sentence case, no emoji, no jargon ("stored readings", "engine", "SFHA" without explanation, "action" stage). Every new en key has an es twin; list the missing vi/zh/ar keys in the report.
4. a11y QA: keyboard-only pass (tab order, focus trapping in Sheets, visible focus), VoiceOver/TalkBack labels on the orb, badges and map text lists, 44px targets, 200% zoom, RTL (ar) layout of the header, chips and sheets (use logical `ms/me/ps/pe` only), contrast spot-checks.
5. Remove the legacy aliases (`--s-*`, `ui.tsx` wrappers) once nothing imports them.
6. Re-shoot `docs/ux/after/` screenshots at 390×844 and 1280×800, with correct filenames.

### 8.4 Backend changes
**None required.** The Home summary (§4.3) and actions (§4.4) are computed client-side from `/risk`, `/flood-history`, `/zip-insurance`, `/alerts` and `/outlook`, which Home already calls (add the `zipInsurance` call to Home; RentBuy already uses it). Optional, not blocking: (a) `/watch/status` could accept `ids` for My place automatically (the frontend can just `POST /watch` My place once and store its id in `floodready.place.v1`); (b) `scripts/demo_check.py --front` selectors may need updating after P1–P5. The backend/test owner should check its front checks for text like "Check my risk", "Demo routes" and "Latency" (the `data-testid="latency"` element now renders only in demo mode, so load with `?demo=1`).

### 8.5 Acceptance checklist (lead verifies)
- [ ] Fresh phone: language → address → household → Home in under 60 seconds; the place persists after reload and appears on Drive (From), Alerts (first place), Prepare, Ask and After a flood (shelter distances).
- [ ] Home first screen (390×844) shows both levels, ≥3 why chips with sources, and the first action card, with no scrolling needed for those.
- [ ] With the demo address: "This place: High exposure", chips "FEMA Zone AE", "Flooded in Harvey (2017)", "ZIP 77096: 6,482 flood claims".
- [ ] No demo control is visible without `?demo=1`; with it, the badge is visible on every screen.
- [ ] No emoji in the UI chrome; all icons are lucide.
- [ ] Every number on screen has a SourceLink within one tap.
- [ ] es parity for all new strings; no truncated labels in es at 360px wide.
- [ ] Lighthouse a11y ≥ 95 on Home, Drive, Ask in both themes.
