#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/deploy/.env"
COMPOSE_FILE="$ROOT/deploy/compose.yaml"

fail() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARNING: $*" >&2; }

command -v docker >/dev/null 2>&1 || fail "docker is required"
docker compose version >/dev/null 2>&1 || fail "docker compose v2 is required"
[[ -f "$ENV_FILE" ]] || fail "copy deploy/.env.example to deploy/.env first"
[[ -f "$COMPOSE_FILE" ]] || fail "missing deploy/compose.yaml"

mode="$(stat -c '%a' "$ENV_FILE" 2>/dev/null || stat -f '%Lp' "$ENV_FILE" 2>/dev/null || true)"
if [[ "$mode" != "600" ]]; then
  warn "deploy/.env permissions are $mode; recommended: chmod 600 deploy/.env"
fi

if grep -q 'CHANGEME_' "$ENV_FILE"; then
  fail "deploy/.env still contains CHANGEME placeholders"
fi

if grep -Eq '^SIGNUPS_ALLOWED=true$' "$ENV_FILE"; then
  warn "public self-registration is enabled"
fi

if grep -Eq '^ADMIN_TOKEN=.+' "$ENV_FILE"; then
  echo "Admin panel: ADMIN_TOKEN configured"
else
  echo "Admin panel: disabled (ADMIN_TOKEN is blank)"
fi

echo "Running Compose configuration validation..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null

echo "GoreeVault preflight passed."
