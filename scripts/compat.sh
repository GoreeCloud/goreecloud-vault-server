#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/tests/compat/compose.yaml"

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

printf '\n==> GoreeVault compatibility: closed-registration phase\n'
cleanup
SIGNUPS_ALLOWED=false docker compose -f "$COMPOSE_FILE" up -d --build --wait --wait-timeout 240
python3 tests/compat/compat.py --mode closed

printf '\n==> GoreeVault compatibility: authenticated CRUD phase\n'
cleanup
SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d --wait --wait-timeout 240
python3 tests/compat/compat.py --mode full

printf '\nGoreeVault compatibility harness passed.\n'
