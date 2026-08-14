#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/deploy/.env"
COMPOSE_FILE="$ROOT/deploy/compose.yaml"

fail() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARNING: $*" >&2; }

env_value() {
  local key="$1"
  sed -n "s/^${key}=//p" "$ENV_FILE" | tail -n 1
}

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

for key in GOREVAULT_DOMAIN POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
  [[ -n "$(env_value "$key")" ]] || fail "$key must not be blank"
done

domain="$(env_value GOREVAULT_DOMAIN)"
postgres_password="$(env_value POSTGRES_PASSWORD)"
admin_token="$(env_value ADMIN_TOKEN)"
smtp_host="$(env_value SMTP_HOST)"
smtp_from="$(env_value SMTP_FROM)"

if (( ${#postgres_password} < 32 )); then
  fail "POSTGRES_PASSWORD must be at least 32 characters"
fi

# The password is embedded in DATABASE_URL. Restrict it to RFC 3986 unreserved
# characters so generated credentials cannot accidentally corrupt the URL.
if [[ ! "$postgres_password" =~ ^[-A-Za-z0-9._~]+$ ]]; then
  fail "POSTGRES_PASSWORD must contain only URL-safe unreserved characters: A-Z a-z 0-9 - . _ ~"
fi

if [[ "$domain" == http://* ]] \
  && [[ "$domain" != http://localhost* ]] \
  && [[ "$domain" != http://127.0.0.1* ]] \
  && [[ "$domain" != http://\[::1\]* ]]; then
  warn "GOREVAULT_DOMAIN uses plain HTTP outside localhost; production must use HTTPS"
fi

if [[ "$domain" == */ ]]; then
  warn "GOREVAULT_DOMAIN has a trailing slash; use the canonical origin without a trailing slash"
fi

if grep -Eq '^SIGNUPS_ALLOWED=true$' "$ENV_FILE"; then
  warn "public self-registration is enabled"
fi

if [[ -n "$admin_token" ]]; then
  if [[ "$admin_token" != \$argon2* && "$admin_token" != \$\$argon2* ]]; then
    fail "ADMIN_TOKEN must be an Argon2 PHC string; plaintext admin passwords are forbidden"
  fi
  echo "Admin panel: Argon2 ADMIN_TOKEN configured"
else
  echo "Admin panel: disabled (ADMIN_TOKEN is blank)"
fi

if [[ -n "$smtp_host" && -z "$smtp_from" ]]; then
  fail "SMTP_FROM must be configured when SMTP_HOST is enabled"
fi

echo "Running Compose configuration validation..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null

echo "GoreeVault preflight passed."
