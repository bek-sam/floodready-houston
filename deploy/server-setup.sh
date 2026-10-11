#!/usr/bin/env bash
# One-time Ubuntu 22.04/24.04 setup. Run on the VPS as root:
#   ssh root@IP 'bash -s' < deploy/server-setup.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl rsync ufw
curl -fsSL https://get.docker.com | sh      # installs docker engine + compose plugin
systemctl enable --now docker
docker compose version
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp   # HTTP/3
ufw --force enable
mkdir -p /opt/floodready
echo "Server ready. Point your domain's A record at this IP, then run deploy.sh locally."
