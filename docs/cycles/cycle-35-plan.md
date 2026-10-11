# Cycle 35 plan — 3 cheap conversions (from cycle-35-coverage.md)
Use ONLY facts/URLs verified in cycle-35-coverage.md.
## FRONTEND
1. G1 buyouts: in the existing buyout UI (RentBuy buyout block / buyout-area card) add the HCFCD Home Buyout Hotline 346-286-4020 (tel: link) + volunteer-for-buyout form link (hcfcd.org/Buyouts), sourced.
2. C4 "Ways to pay less for flood insurance" block on Prepare › Insurance using only the FloodSmart elevation-certificate/elevation wording verified in the doc; link FloodSmart.
3. E5 airport chip on Drive: GET /api/airports/status (exists: {airports[{code,closed,reason,reopen}], source, meta, note}); show "IAH/HOU: open" or closure reason + reopen; hide when closed is null; FAA source link.
Strings in src/i18n/p35.ts (5 languages).
## DATA
data/knowledge: add the buyout hotline/volunteer form to the buyouts card and the elevation-certificate ways-to-save to the insurance card (verified facts only, source lines).
