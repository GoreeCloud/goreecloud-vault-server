#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${GOREVAULT_TEST_URL:-http://127.0.0.1:8080}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

curl_json() {
  local url="$1"
  local output="$2"
  shift 2
  curl --fail --silent --show-error \
    --connect-timeout 5 \
    --max-time 15 \
    "$@" \
    "$url" >"$output"
}

# Gate A1: the public health endpoint must verify both HTTP service and DB connectivity.
curl_json "$BASE_URL/alive" "$TMP_DIR/alive.json"
python3 - "$TMP_DIR/alive.json" <<'PY'
import json
import pathlib
import sys

value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert isinstance(value, str) and value.strip(), "alive response must be a non-empty JSON string"
PY
pass "DB-backed /alive health check"

curl --fail --silent --show-error --head \
  --connect-timeout 5 --max-time 15 \
  "$BASE_URL/alive" >/dev/null
pass "HEAD /alive contract"

curl_json "$BASE_URL/api/alive" "$TMP_DIR/api-alive.json"
pass "DB-backed /api/alive health check"

# Gate A2: clients must receive coherent GoreeVault self-hosted server metadata.
curl_json "$BASE_URL/api/config" "$TMP_DIR/config.json"
python3 - "$TMP_DIR/config.json" <<'PY'
import json
import pathlib
import sys

config = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert isinstance(config, dict), "config response must be an object"
assert config.get("object") == "config", "config object marker changed"
assert config.get("server", {}).get("name") == "GoreeVault", "server identity must be GoreeVault"
assert config.get("settings", {}).get("disableUserRegistration") is True, "CI stack must keep public registration disabled"
environment = config.get("environment", {})
assert str(environment.get("api", "")).endswith("/api"), "API URL missing from config"
assert str(environment.get("identity", "")).endswith("/identity"), "identity URL missing from config"
PY
pass "self-hosted config and GoreeVault identity"

# Gate A3: prelogin must remain Bitwarden-client compatible for an unknown account.
curl_json \
  "$BASE_URL/identity/accounts/prelogin" \
  "$TMP_DIR/prelogin.json" \
  --header 'Content-Type: application/json' \
  --request POST \
  --data '{"email":"goreevault-ci@example.invalid"}'
python3 - "$TMP_DIR/prelogin.json" <<'PY'
import json
import pathlib
import sys

prelogin = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert isinstance(prelogin, dict), "prelogin response must be an object"
assert "kdf" in prelogin, "prelogin response is missing kdf"
assert "kdfIterations" in prelogin, "prelogin response is missing kdfIterations"
PY
pass "prelogin compatibility contract"

# Gate A4: closed registration is a security policy, not merely documentation.
register_status="$({
  curl --silent --show-error \
    --connect-timeout 5 \
    --max-time 15 \
    --output "$TMP_DIR/register.json" \
    --write-out '%{http_code}' \
    --header 'Content-Type: application/json' \
    --request POST \
    --data '{"email":"goreevault-ci@example.invalid","name":"GoreeVault CI"}' \
    "$BASE_URL/identity/accounts/register/send-verification-email"
} || true)"

if [[ ! "$register_status" =~ ^4[0-9][0-9]$ ]]; then
  cat "$TMP_DIR/register.json" >&2 2>/dev/null || true
  fail "closed registration expected a 4xx response, got ${register_status:-no-status}"
fi
pass "public registration remains closed"

# Gate A5: unauthenticated callers must not be able to sync vault data.
sync_status="$({
  curl --silent --show-error \
    --connect-timeout 5 \
    --max-time 15 \
    --output "$TMP_DIR/sync.json" \
    --write-out '%{http_code}' \
    "$BASE_URL/api/sync"
} || true)"

case "$sync_status" in
  401|403) pass "unauthenticated vault sync is denied" ;;
  *)
    cat "$TMP_DIR/sync.json" >&2 2>/dev/null || true
    fail "unauthenticated /api/sync expected 401 or 403, got ${sync_status:-no-status}"
    ;;
esac

printf '\nGoreeVault compatibility smoke suite passed.\n'
