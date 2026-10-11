# Sponsor stack setup (facts marked "unverified" came from search snippets/memory; I found no CodeRED 2026 sponsor page - uhcode.red lists no perks. Check the Devpost/Discord for each sponsor's claim code.)

## Tiger Data (Timescale Cloud)
1. https://console.cloud.timescale.com (Tiger Console; Tiger Data = renamed Timescale) -> sign up -> Create service -> choose **Free** (us-east-1 only, beta) or the 30-day trial (docs conflict: unthrottled trial vs ~$1,000 credit).
2. Free-tier limits: fixed small CPU/RAM, no pooling/replication/VPC, **goes read-only when storage fills**, can upgrade anytime. Includes TimescaleDB + pgvector + pgvectorscale (per docs).
3. Download the connection info / `.env` file from the service page. Format: `postgres://tsdbadmin:PASSWORD@HOST.tsdb.cloud.timescale.com:PORT/tsdb?sslmode=require`. For SQLAlchemy+psycopg3 use `postgresql+psycopg://...`.
4. SQL: `CREATE EXTENSION IF NOT EXISTS timescaledb; CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;` (if one errors, skip it; app falls back).
5. Hypertable: `SELECT create_hypertable('reports','created_at');` (PK must include the time column -> composite PK `(id, created_at)`) and same for gauge readings.
6. Vector index: `CREATE INDEX ON chunks USING diskann (embedding vector_cosine_ops);` or plain `hnsw`. Gemini embedding dim: gemini-embedding-001 default 3072 - request `output_dimensionality=768` to keep indexes small.
7. IP allowlist: free services are reachable from anywhere over TLS; Vultr needs no setup.

## Vultr
- Fastest: Cloud Compute (Regular, $6/mo, 1 vCPU/1 GB) **Ubuntu 24.04**, region Dallas/Atlanta. Free credit: Vultr gives new accounts trial credit (amount varies, unverified) and MLH/event codes are distributed by the organizers - ask on Discord/Devpost; redeem at Billing -> Promo Code.
- Steps (≈15 min): `ssh root@IP` -> `apt update && apt install -y docker.io docker-compose-plugin caddy git` (or skip docker: `curl -LsSf https://astral.sh/uv/install.sh | sh`) -> clone repo -> `cd backend && uv sync && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000` under a systemd unit -> build frontend locally (`npm run build`) and serve `frontend/dist` with Caddy.
- Caddyfile (domain A record -> VPS IP, ports 80/443 open: `ufw allow 80,443/tcp`):
```
floodready.example.tech {
  encode gzip
  handle /api/* { reverse_proxy 127.0.0.1:8000 }
  handle { root * /srv/floodready/dist
           try_files {path} /index.html
           file_server }
}
```
Caddy auto-provisions Let's Encrypt HTTPS once DNS resolves.

## GoDaddy Registry (via MLH)
- MLH historically gives hackers a free 1-year domain on GoDaddy Registry TLDs through a claim page (e.g. .tech, .xyz-family, .online, .space, .store - exact list unverified). Claim: the organizers' MLH hacker-pack/Devpost page gives a code or link -> pick the domain -> enter code at checkout -> set A record to the Vultr IP (TTL 300). Ask organizers if the link isn't visible.
- Fallback: use the raw IP with `sslip.io` (`1-2-3-4.sslip.io` works with Caddy HTTPS).

## ElevenLabs
- Free plan: 10,000 credits/month (~10 min of multilingual v2; Flash v2.5 costs ~0.5 credit/char -> ~20 min), no commercial license, attribution expected, third-party figures (unverified). Models: `eleven_multilingual_v2` (~29 langs, 10k chars/request), `eleven_flash_v2_5` (~32 langs, fast, cheaper). Use flash_v2_5 for alerts.
- Key: https://elevenlabs.io -> profile -> API Keys (set restrictions: text-to-speech only). Python: `client.text_to_speech.convert(voice_id=..., text=..., model_id="eleven_flash_v2_5", output_format="mp3_44100_128")`. Use a premade voice (e.g. Rachel `21m00Tcm4TlvDq8ikWAM`).
- **Cache MP3 per (text,lang)** and pre-generate demo phrases (EN/ES/VI/ZH/AR) to avoid burning credits. Fallback: browser speechSynthesis.

## Gemini
- Key: https://aistudio.google.com/apikey (free, no card). `GEMINI_API_KEY`.
- Free limits are per-project and no longer published as one table; third-party (Jan 2026): 2.5 Flash ~10 RPM / 250 RPD, Flash-Lite ~30 RPM / 1,000 RPD. Check your live quota at https://aistudio.google.com/rate-limit. I could not confirm the current free status of `gemini-embedding-001` or whether newer defaults exist: run `GET https://generativelanguage.googleapis.com/v1beta/models?key=KEY` once and confirm `gemini-2.5-flash` and `gemini-embedding-001` appear.
- Mitigations: cache plans by profile hash, batch-embed knowledge at build time (store vectors in repo/DB), retry with backoff on 429, template fallback.

## Backboard
- https://app.backboard.io -> sign up -> Settings -> API Keys. New accounts get $5 free credit for 30 days (FAQ, via search). Docs: https://docs.backboard.io/sdk/quickstart.
- REST base `https://app.backboard.io/api`, header `X-API-Key`. Create assistant once (name/system prompt), create a thread per household, `POST /threads/{thread_id}/messages` with `memory: "Auto"` (form field) so facts are stored/retrieved; memory is per **assistant**, so use one assistant_id per household (or per app + user-scoped threads). Quickstart shortcut: `POST /threads/messages` without ids auto-creates both. Endpoint details unverified - read docs/api-reference/threads/send-message before coding. Fallback: local DB profile.

## Solana (worth it?)
- Cheapest integration: devnet **Memo** program tx with the SHA-256 hash of a community report. `solana-keygen new`, `solana airdrop 2 --url devnet` (faucet https://faucet.solana.com if rate-limited), program id `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`. Python: `solders` + `solana` (`pip install solana`), build a Transaction with one Memo instruction, send via `https://api.devnet.solana.com`, store signature, link `https://explorer.solana.com/tx/<sig>?cluster=devnet`.
- Worth it only as a Tier-3 stretch (~45 min): 1 server-side keypair, async fire-and-forget after saving the report, never block the user. Skip unless a Solana track prize is explicitly offered.

## DEV (writing challenge)
- Monthly MLH x DEV challenge: build at an MLH event, publish a post on DEV about the project and what you learned, include tag `#mlhacks` (https://dev.to/mlh-hackathon; exact window/prizes/rules not visible - open the page, "Current challenge window" is in ET). Other open challenge (Hacktoberfest Week 1, ends Oct 11 11:59 PM PDT) requires open-source AI at the core - not obviously ours; https://dev.to/challenges/hf26.
- Post must cover what/who/demo/lessons; keep a 600-word outline ready, publish before the window closes.

## Deploy checklist
1. DNS A record -> Vultr IP; `dig +short domain` matches.
2. Backend `.env` on server: `DATABASE_URL` (Tiger, `sslmode=require`), `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`, `GEMINI_EMBED_MODEL=gemini-embedding-001`, `ELEVENLABS_API_KEY`, `BACKBOARD_API_KEY`, `CORS_ORIGINS=https://yourdomain`. Never commit.
3. FastAPI CORS: allow the domain origin; if same-origin via Caddy `/api` proxy, CORS is unnecessary (preferred).
4. systemd service for uvicorn (`Restart=always`), Caddy reload, `ufw allow 22,80,443`.
5. Smoke test: `curl https://domain/api/health`, geocode + risk for a Houston address, one /voice call, open site on phone.
6. Keep a pre-warmed cache of demo addresses; test with keys unset (fallback path) before the demo.
