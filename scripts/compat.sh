#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/tests/compat/compose.yaml"

cleanup() {
  docker compose -f "$COMPOSE_FILE" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd "$ROOT_DIR"

printf '\n==> GoreeVault compatibility: closed-registration phase\n'
cleanup
SIGNUPS_ALLOWED=false docker compose -f "$COMPOSE_FILE" up -d --build --wait postgres
SIGNUPS_ALLOWED=false docker compose -f "$COMPOSE_FILE" up -d server
python3 tests/compat/compat.py --mode closed

printf '\n==> GoreeVault compatibility: authenticated CRUD phase\n'
cleanup
SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d --build --wait postgres
SIGNUPS_ALLOWED=true docker compose -f "$COMPOSE_FILE" up -d server
python3 tests/compat/compat.py --mode full

printf '\nGoreeVault compatibility harness passed.\n'
