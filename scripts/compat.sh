#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/tests/compat/compose.yaml"
PHASE="${1:-all}"

cleanup() {
  docker compose -f "$COMPOSE_FILE" down --volumes --remove-orphans >/dev/null 2>&1 || true
}

show_logs() {
  printf '\n==> GoreeVault compatibility failure logs\n' >&2
  docker compose -f "$COMPOSE_FILE" ps >&2 || true
  docker compose -f "$COMPOSE_FILE" logs --no-color --tail=250 >&2 || true
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
docker compose -f "$COMPOSE_FILE" config >/dev/null

run_closed() {
  printf '\n==> GoreeVault compatibility: closed-registration phase\n'
  cleanup
  SIGNUPS_ALLOWED=false docker compose -f "$COMPOSE_FILE" up -d --wait --wait-timeout 240
  python3 tests/compat/compat.py --mode closed
}

run_full() {
  printf '\n==> GoreeVault compatibility: authenticated CRUD phase\n'
  cleanup
  SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d --wait --wait-timeout 240
  python3 tests/compat/compat.py --mode full
}

run_org_members() {
  printf '\n==> GoreeVault compatibility: restricted organization member phase\n'
  cleanup
  SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d --wait --wait-timeout 240
  python3 tests/compat/org_members.py
}

run_import_export() {
  printf '\n==> GoreeVault compatibility: import and export phase\n'
  cleanup
  SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d --wait --wait-timeout 240
  python3 tests/compat/import_export.py
}

run_totp() {
  printf '\n==> GoreeVault compatibility: TOTP authentication phase\n'
  cleanup
  SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d --wait --wait-timeout 240
  python3 tests/compat/totp.py
}

run_webauthn() {
  printf '\n==> GoreeVault compatibility: WebAuthn challenge phase\n'
  cleanup
  DOMAIN=http://localhost:18080 SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d --wait --wait-timeout 240
  python3 tests/compat/webauthn.py
}

case "$PHASE" in
  closed) run_closed ;;
  full) run_full ;;
  org-members) run_org_members ;;
  import-export) run_import_export ;;
  totp) run_totp ;;
  webauthn) run_webauthn ;;
  all)
    run_closed
    run_full
    run_org_members
    run_import_export
    run_totp
    run_webauthn
    ;;
  *)
    echo "Usage: $0 [closed|full|org-members|import-export|totp|webauthn|all]" >&2
    exit 2
    ;;
esac

printf '\nGoreeVault compatibility phase %s passed.\n' "$PHASE"
