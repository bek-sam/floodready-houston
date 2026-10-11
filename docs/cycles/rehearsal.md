# Demo rehearsal (Oct 11, fresh context, /?demo=1, 1280x900 and 390x844)

Scripts and screenshots: scratchpad e2e/rehearsal/ (s*.py, *.png). /ask calls used: 2 (ES question, desktop and mobile; both answered in about 0.5 s with sourced steps). No reports, votes or pushes sent. Console errors: 0. HTTP >=400: 0.
Voice was tested with Chromium fake mic only; no real speech, no answer heard.

## Per-step results
| # | Step | 1280 | 390 | Time | Notes |
|---|---|---|---|---|---|
| 0 | Open /?demo=1 | PASS | PASS | 3.3 s load | Demo badge and demo controls show. Slow-ish first paint. |
| 1 | My Risk: 5300 N Braeswood | PASS | PASS | about 0.5-1 s to summary | Zone AE, Flooded in Harvey, ZIP 77096: 6,482 claims chip. Harvey major, median premium $1,501 are inside collapsed cards (Flood history 2.5 s incl. wait, Renting or buying). The summary chip says "Major flooding ... Tax Day Flood (2016)", not Harvey. |
| 2 | Drive: Allen Parkway chip, Simulate storm, Check route | PASS | PASS | chip 1.0 s, route about 1 s | "Avoid this route - Simulated" with 4 named crossings. On mobile the badge truncates ("Avoid this route - Simula..."). From field shows the chip label, not an address. |
| 3 | Replay Harvey, Play, Narrate | PASS | PASS | page 3.6 s | Harvey preselected. Play advances 1 day per 2 s. Narrate works (button turns to Stop narration). Times shown in browser time zone. Clock ran to 9/2/2017 after the event end of Sep 1. |
| 4 | Seabrook, TX 77586 | PARTIAL | PARTIAL | 1.5 s | Zone VE, ZIP claims, "Hurricane evacuation zone A", "Up to 9+ ft surge (Cat 3+)", Galveston tide card all present. "No Harvey extent data" is NOT in the summary, only inside the "Your place's flood profile" card. See bugs 3 and 4. |
| 5 | Voice: Ask, Voice | PARTIAL | PARTIAL | WS connect about 2 s | The control is labelled "Talk", not "Voice". It connected and showed Listening / Hearing you. Not verified with real speech. |
| 6 | Ask in Spanish | PASS | PASS | 0.5 s | Sourced steps, 911 in step 1 and in the footer, sources listed. |
| 7 | Watch: Simulate storm push | NOT TESTED | NOT TESTED | - | Page is #alerts. Buttons are "Send test alert" and "Simulate storm alert". Both are disabled in a fresh browser: "Notifications are blocked / Turn on alerts on this phone to send a test". Not run, per instructions. |
| 7b | Judge SMS: ALERTS ON 77096 | PASS | PASS | 1.6 s | Reply is saved, none sent yet. |
| 8 | Judge page, Go, Reset demo | PASS | PASS | 3.2 s | Reset demo sets the Braeswood place and goes to #home. |

## Bugs (ranked)
1. MEDIUM - "Storm mode: refreshing every 1-2 min" chip shows on Home, Alerts and Seabrook while everything reads Normal and Simulate storm is off. The cause is the global `freshness.mark_storm()` flag: it lasts 180 s, is shared by all clients, and was still on 2+ minutes after my last simulated run (/status storm_mode flipped to True). A judge will ask "what storm?". Repro: run the Drive simulated route, then open #alerts. I could not isolate whether a real trigger or my simulation set it. Files: backend/app/freshness.py (mark_storm), services/gauges.py:99, services/alerts.py:18,93,154. The UI chip is in frontend/src/components/ds (Freshness).
2. MEDIUM - After saving a place, the "My place" side sheet stays open and covers the page (a toast says "Place saved"). Clicks on the page behind it are blocked until Esc or X. Repro: Set my place, type address, Enter. File: frontend AddressForm.tsx and the place sheet in components/shell.
3. LOW-MED - The Seabrook summary has no Harvey line, so "no false all-clear" is invisible unless "Your place's flood profile" is expanded. The script claims it is in the summary.
4. LOW - Seabrook nearby-gauge list: "Tide Station (HGX) at Morgan's Point 2.08 ft - Normal - No recent readings" is a contradictory row. It is also 8.4 mi away and the closest gauge. Source: data/gauges.json and the gauge card in frontend/src/components/ds (GaugeChips).
5. LOW - Voice panel on a fresh visit shows the old heading "Tap to talk / Tap again to stop" above a "Hold to talk or hold the space bar" control (contradictory). With no place set, the live session starts without lat/lon, so "Did my neighborhood flood?" has no place unless step 1 was done in the same tab. File: frontend/src/pages/Ask.tsx, components/LiveTalk.tsx.
6. LOW - The summary chip highlights the Tax Day (2016) flood while the script says Harvey; both are Major.
7. LOW - Replay clock shows the browser time zone and runs past the event end date (9/2 vs Sep 1). File: frontend/src/pages/Replay.tsx.
8. LOW - Mobile Drive: From field shows the chip label ("Downtown: Allen Parkway under...") and the verdict pill is truncated.
9. INFO - Slow first loads of about 3 s on #home, #replay, #alerts and #judge.

## Script edits needed (DEMO-DAY.md)
- Step 1: there is no "My Risk" tab. Use Home, then "Set my place" (or "Try a sample address"). Close the My place sheet with Esc. "Harvey: major" and "$1,501" are inside the collapsed "Flood history here" and "Renting or buying here?" cards, so say "expand".
- Step 2: the chip is labelled "Downtown: Allen Parkway underpass". Simulate storm is a toggle on the Drive page.
- Step 4: "No Harvey extent data" is inside "Your place's flood profile" (expand it), not in the summary. The surge chip reads "Up to 9+ ft storm surge (Cat 3+)" and the Galveston tide appears as a card on the page, not a chip.
- Step 5: the toggle is "Type / Talk", not "Voice". Tap the mic, then hold to talk or hold space. The "Switch to Standard" wording is now "Switch to typing".
- Step 7: use #alerts, "Simulate storm alert". It needs notification permission and is disabled otherwise. Enable first in Chrome (Alerts on this phone toggle).
- The Judge page lists 5 steps (Risk, Avoid, Replay, Spanish, Push), so Seabrook and Voice are not in its guided script.
- Spanish answer step: switch the language to Español first (the EN menu, top right).
