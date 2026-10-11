# AI eval (citations)

Run: 2026-10-11 01:00:05 against `http://localhost:8000`. **Pass rate: 29/30 (97%)**

| Group | Pass | Total |
|---|---|---|
| endpoint: ask | 14 | 15 |
| endpoint: stream | 15 | 15 |
| lang: en | 19 | 20 |
| lang: es | 6 | 6 |
| lang: vi | 2 | 2 |
| lang: zh | 2 | 2 |
| cat: cite | 29 | 30 |

## Failure types

- no citations: 1

## Failures

### cite-en-14 [ask] (753 ms, gemini)
Q: What FEMA flood zone am I in and what does it mean?
Failed: no citations

```
You are in FEMA flood zone AE, which is a Special Flood Hazard Area where flood insurance is typically required with a federally backed mortgage. Being in this zone means you are in an area with a high risk of flooding. Not being in a flood zone also does not mean you are safe, as the lines on a FEMA map are often actuarial rather than physical.
Not official guidance. In danger, call 911.
```
