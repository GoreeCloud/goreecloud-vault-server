#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/tests/recovery/compose.yaml"
RECOVERY_TEST="$ROOT_DIR/tests/recovery/recovery.py"
TMP_DIR="$(mktemp -d)"
STATE_FILE="$TMP_DIR/state.json"
DB_DUMP="$TMP_DIR/postgres.dump"
DATA_ARCHIVE="$TMP_DIR/data.tar"
RESTORED_ARCHIVE="$TMP_DIR/data-restored.tar"
ORIGINAL_DATA="$TMP_DIR/original-data"
RESTORED_DATA="$TMP_DIR/restored-data"

compose() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

cleanup() {
  compose down --volumes --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$TMP_DIR"
}

show_logs() {
  printf '\n==> GoreeVault recovery failure logs\n' >&2
  compose ps >&2 || true
  compose logs --no-color --tail=250 >&2 || true
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

printf '\n==> GoreeVault recovery: start clean seed environment\n'
compose down --volumes --remove-orphans >/dev/null 2>&1 || true
SIGNUPS_ALLOWED=true compose up -d --build --wait
python3 "$RECOVERY_TEST" --mode seed --state "$STATE_FILE"

printf '\n==> GoreeVault recovery: quiesce application before backup\n'
compose stop server

printf '\n==> GoreeVault recovery: capture PostgreSQL logical backup\n'
compose exec -T postgres \
  pg_dump \
    --format=custom \
    --no-owner \
    --no-privileges \
    -U goreevault_recovery \
    -d goreevault_recovery >"$DB_DUMP"
test -s "$DB_DUMP"

printf '\n==> GoreeVault recovery: capture complete /data volume\n'
compose run --rm -T --no-deps --entrypoint tar server -C /data -cf - . >"$DATA_ARCHIVE"
test -s "$DATA_ARCHIVE"
mkdir -p "$ORIGINAL_DATA"
tar -xf "$DATA_ARCHIVE" -C "$ORIGINAL_DATA"
if ! find "$ORIGINAL_DATA" -type f -print -quit | grep -q .; then
  echo "ERROR: /data backup did not contain any files" >&2
  exit 1
fi

printf '\n==> GoreeVault recovery: destroy original database and data volumes\n'
compose down --volumes --remove-orphans

printf '\n==> GoreeVault recovery: create fresh PostgreSQL volume\n'
compose up -d --wait postgres

printf '\n==> GoreeVault recovery: restore PostgreSQL into fresh database\n'
compose exec -T postgres \
  pg_restore \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    -U goreevault_recovery \
    -d goreevault_recovery <"$DB_DUMP"

printf '\n==> GoreeVault recovery: restore /data into fresh volume before server start\n'
compose run --rm -T --no-deps --entrypoint tar server -C /data -xf - <"$DATA_ARCHIVE"

printf '\n==> GoreeVault recovery: boot restored GoreeVault\n'
SIGNUPS_ALLOWED=true compose up -d --wait server
python3 "$RECOVERY_TEST" --mode verify --state "$STATE_FILE"

printf '\n==> GoreeVault recovery: verify every backed-up /data file is byte-identical\n'
compose run --rm -T --no-deps --entrypoint tar server -C /data -cf - . >"$RESTORED_ARCHIVE"
mkdir -p "$RESTORED_DATA"
tar -xf "$RESTORED_ARCHIVE" -C "$RESTORED_DATA"

while IFS= read -r -d '' original_file; do
  relative_path="${original_file#"$ORIGINAL_DATA"/}"
  restored_file="$RESTORED_DATA/$relative_path"
  if [[ ! -f "$restored_file" ]]; then
    echo "ERROR: restored /data is missing $relative_path" >&2
    exit 1
  fi
  cmp --silent "$original_file" "$restored_file" || {
    echo "ERROR: restored /data file differs: $relative_path" >&2
    exit 1
  }
done < <(find "$ORIGINAL_DATA" -type f -print0)

printf '\nPASS  GoreeVault PostgreSQL + /data destruction/restore rehearsal passed.\n'
