# AI eval (quick)

Run: 2026-10-11 01:20:31 against `http://localhost:8000`. **Pass rate: 38/40 (95%)**

| Group | Pass | Total |
|---|---|---|
| endpoint: ask | 19 | 20 |
| endpoint: stream | 19 | 20 |
| lang: en | 26 | 26 |
| lang: es | 12 | 14 |
| cat: adv | 2 | 2 |
| cat: buy | 4 | 4 |
| cat: drive | 4 | 4 |
| cat: emerg | 4 | 4 |
| cat: hist | 4 | 4 |
| cat: ins | 4 | 4 |
| cat: med | 4 | 4 |
| cat: oos | 2 | 2 |
| cat: post | 4 | 4 |
| cat: rent | 2 | 4 |
| cat: shel | 4 | 4 |

## Failure types

- missing any of required terms: 2

## Failures

### rent-es-1 [ask] (241 ms, template)
Q: Soy inquilino y mi arrendador no me dijo que el apartamento se inundó antes, ¿cuáles son mis derechos?
Failed: missing any of required terms

```
Esto es lo más útil para su pregunta, según nuestras fuentes (los textos citados están en inglés):
Qué hacer:
1. Renters should ask the landlord about past flooding in writing, consider renters insurance with a separate flood policy, and know where to call. [1] (fuente en inglés)
Esto no es una guía oficial. En una emergencia, llame al 911.
```

### rent-es-1 [stream] (351 ms, template)
Q: Soy inquilino y mi arrendador no me dijo que el apartamento se inundó antes, ¿cuáles son mis derechos?
Failed: missing any of required terms

```
Esto es lo más útil para su pregunta, según nuestras fuentes (los textos citados están en inglés):
Qué hacer:
1. Renters should ask the landlord about past flooding in writing, consider renters insurance with a separate flood policy, and know where to call. [1] (fuente en inglés)
Esto no es una guía oficial. En una emergencia, llame al 911.
```
