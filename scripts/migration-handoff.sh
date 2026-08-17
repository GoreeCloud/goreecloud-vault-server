#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/tests/migration/compose.yaml"
RECOVERY_TEST="$ROOT_DIR/tests/recovery/recovery.py"
BASE_URL="http://127.0.0.1:18082"
TMP_DIR="$(mktemp -d)"
STATE_FILE="$TMP_DIR/state.json"

compose() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

cleanup() {
  compose down --volumes --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$TMP_DIR"
}

show_logs() {
  printf '\n==> GoreeVault migration handoff failure logs\n' >&2
  compose ps >&2 || true
  compose logs --no-color --tail=300 >&2 || true
}

on_exit() {
  local status=$?
  if [[ $status -ne 0 ]]; then
    show_logs
  fi
  cleanup
}
trap on_exit EXIT

cd "$ROOT_DIR"

printf '\n==> Migration rehearsal: start exact upstream Vaultwarden baseline\n'
compose down --volumes --remove-orphans >/dev/null 2>&1 || true
compose up -d --wait --wait-timeout 240 postgres
compose up -d --wait --wait-timeout 240 upstream

printf '\n==> Migration rehearsal: seed upstream Vaultwarden through public APIs\n'
GOREVAULT_RECOVERY_URL="$BASE_URL" python3 "$RECOVERY_TEST" --mode seed --state "$STATE_FILE"

printf '\n==> Migration rehearsal: stop upstream and hand storage to GoreeVault\n'
compose stop upstream
compose up -d --build --wait --wait-timeout 300 goreevault

printf '\n==> Migration rehearsal: verify upstream data under GoreeVault\n'
GOREVAULT_RECOVERY_URL="$BASE_URL" python3 "$RECOVERY_TEST" --mode verify --state "$STATE_FILE"
python3 - "$BASE_URL" <<'PY'
import json
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1] + "/api/config", timeout=15) as response:
    body = json.load(response)
assert body.get("server", {}).get("name") == "GoreeVault", body
assert body.get("settings", {}).get("disableUserRegistration") is True, body
print("PASS  migrated instance reports GoreeVault identity and closed registration")
PY

printf '\n==> Rollback rehearsal: stop GoreeVault and return storage to upstream baseline\n'
compose stop goreevault
compose up -d --wait --wait-timeout 240 upstream

printf '\n==> Rollback rehearsal: verify the same data under upstream Vaultwarden again\n'
GOREVAULT_RECOVERY_URL="$BASE_URL" python3 "$RECOVERY_TEST" --mode verify --state "$STATE_FILE"

printf '\nPASS  Vaultwarden -> GoreeVault -> Vaultwarden storage handoff rehearsal passed.\n'
