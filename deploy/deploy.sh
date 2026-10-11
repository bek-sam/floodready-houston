#!/usr/bin/env bash
# Run LOCALLY:  VPS=root@1.2.3.4 DOMAIN=floodready.tech ./deploy/deploy.sh
# Builds the frontend, rsyncs the repo to the VPS, and (re)starts the stack.
set -euo pipefail
: "${VPS:?set VPS=user@ip}"
: "${DOMAIN:?set DOMAIN=your.domain (A record must point at the VPS)}"
REMOTE_DIR="${REMOTE_DIR:-/opt/floodready}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[ -f .env ] || { echo "Missing $ROOT/.env (copy .env.example and fill keys)"; exit 1; }

echo "==> Building frontend"
(cd frontend && npm ci && npm run build)

echo "==> Syncing to $VPS:$REMOTE_DIR"
ssh "$VPS" "mkdir -p $REMOTE_DIR"
rsync -az --delete \
  --exclude node_modules --exclude .venv --exclude .git --exclude '*.db' \
  --exclude __pycache__ --exclude backend/.cache --exclude .vapid.json \
  --exclude frontend/src --exclude frontend/public \
  ./ "$VPS:$REMOTE_DIR/"

echo "==> Starting containers"
ssh "$VPS" "cd $REMOTE_DIR/deploy && DOMAIN=$DOMAIN docker compose up -d --build && docker compose ps"

echo "==> Done. Smoke test: curl https://$DOMAIN/api/health"
