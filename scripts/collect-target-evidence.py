#!/usr/bin/env python3
"""Collect the GoreeVault target-environment Stable evidence section.

This collector is intentionally read-only. It inspects the reviewed production
contract and live Docker metadata, performs a minimal HTTPS health check, and
combines those machine-observed facts with explicit operator attestations for
controls that cannot be proven safely from container metadata alone.

It never serializes container environment values, database credentials, vault
contents, cookies, tokens, recovery material, or other reusable secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
IMAGE_DIGEST_RE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")
EXPECTED_ORIGIN = "https://vault.goreecloud.com"
REQUIRED_MANUAL_FLAGS = (
    "reverse_proxy_https_wss",
    "backup_created",
    "restore_rehearsed",
    "rollback_recorded",
    "monitoring_verified",
    "logs_reviewed_for_sensitive_data",
    "netbird_path_verified",
)


class EvidenceError(RuntimeError):
    """Raised when target-environment evidence cannot be proven safely."""


def fail(message: str) -> "NoReturn":
    raise EvidenceError(message)


def run(command: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as exc:
        fail(f"required command is unavailable: {command[0]}")
        raise AssertionError from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        fail(f"command failed: {' '.join(command)}{suffix}")
        raise AssertionError from exc


def load_json_command(command: list[str]) -> Any:
    result = run(command)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"command did not return valid JSON: {' '.join(command)}")
        raise AssertionError from exc


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        fail(f"production environment file does not exist: {path}")

    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        fail(f"production environment file must not be group/world accessible: {path} mode={mode:04o}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def env_map(inspect: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for entry in inspect.get("Config", {}).get("Env") or []:
        if "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        values[key] = value
    return values


def inspect_container(name: str) -> dict[str, Any]:
    payload = load_json_command(["docker", "inspect", name])
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        fail(f"unexpected docker inspect result for {name}")
    return payload[0]


def image_is_digest_pinned(image: str) -> bool:
    return bool(IMAGE_DIGEST_RE.fullmatch(image))


def backend_is_loopback_only(inspect: dict[str, Any]) -> bool:
    ports = inspect.get("NetworkSettings", {}).get("Ports") or {}
    published: list[dict[str, Any]] = []
    for bindings in ports.values():
        if bindings:
            published.extend(binding for binding in bindings if isinstance(binding, dict))
    return bool(published) and all(binding.get("HostIp") == "127.0.0.1" for binding in published)


def postgres_is_internal_only(inspect: dict[str, Any]) -> bool:
    ports = inspect.get("NetworkSettings", {}).get("Ports") or {}
    return all(not bindings for bindings in ports.values())


def server_is_non_root(inspect: dict[str, Any]) -> bool:
    user = str(inspect.get("Config", {}).get("User") or "").strip()
    if not user:
        return False
    primary = user.split(":", 1)[0].strip()
    if primary.lower() == "root":
        return False
    if primary.isdigit():
        return int(primary) > 0
    return primary not in {"0", ""}


def root_filesystem_is_read_only(inspect: dict[str, Any]) -> bool:
    return inspect.get("HostConfig", {}).get("ReadonlyRootfs") is True


def capabilities_are_dropped(inspect: dict[str, Any]) -> bool:
    cap_drop = inspect.get("HostConfig", {}).get("CapDrop") or []
    return any(str(value).upper() == "ALL" for value in cap_drop)


def no_new_privileges_enabled(inspect: dict[str, Any]) -> bool:
    security_opt = inspect.get("HostConfig", {}).get("SecurityOpt") or []
    normalized = {str(value).lower() for value in security_opt}
    return any(
        value == "no-new-privileges" or value.startswith("no-new-privileges:true")
        for value in normalized
    )


def registration_is_closed(inspect: dict[str, Any]) -> bool:
    value = env_map(inspect).get("SIGNUPS_ALLOWED", "").strip().lower()
    return value in {"false", "0", "no", "off"}


def admin_is_disabled(inspect: dict[str, Any]) -> bool:
    value = env_map(inspect).get("ADMIN_TOKEN")
    return value is None or value.strip() == ""


def validate_reference(name: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned or "REPLACE_ME" in cleaned:
        fail(f"{name} must be a real non-placeholder reference")
    if any(char in cleaned for char in "\r\n"):
        fail(f"{name} must be a single-line reference")
    return cleaned


def validate_previous_image(value: str) -> str:
    cleaned = value.strip()
    if not image_is_digest_pinned(cleaned):
        fail("previous-known-good-image must be an immutable image@sha256:<64-hex> reference")
    return cleaned


def verify_contract(repository_root: Path) -> None:
    validator = repository_root / "scripts" / "validate-production-deployment.sh"
    if not validator.is_file():
        fail(f"production deployment validator not found: {validator}")
    result = run(["bash", str(validator)], capture=True)
    if result.returncode != 0:
        fail("production deployment source contract validation failed")


def verify_compose_renders(repository_root: Path, env_file: Path, compose_file: Path) -> None:
    absolute_compose = compose_file if compose_file.is_absolute() else repository_root / compose_file
    if not absolute_compose.is_file():
        fail(f"production Compose file not found: {absolute_compose}")
    run(
        [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "-f",
            str(absolute_compose),
            "config",
            "--quiet",
        ],
        capture=True,
    )


def verify_https_origin(origin: str, timeout_seconds: int) -> None:
    if origin != EXPECTED_ORIGIN:
        fail(f"origin must be exactly {EXPECTED_ORIGIN}")
    run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--output",
            os.devnull,
            "--max-time",
            str(timeout_seconds),
            f"{origin}/alive",
        ],
        capture=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect the target_environment section for GoreeVault Stable evidence."
    )
    parser.add_argument("--env-file", required=True, type=Path)
    parser.add_argument("--repository-root", default=Path.cwd(), type=Path)
    parser.add_argument("--compose-file", default=Path("deploy/compose.production.yaml"), type=Path)
    parser.add_argument("--goreevault-container", default="goreevault")
    parser.add_argument("--postgres-container", default="goreevault-postgres")
    parser.add_argument("--origin", default=EXPECTED_ORIGIN)
    parser.add_argument("--expected-manifest-digest", required=True)
    parser.add_argument("--previous-known-good-image", required=True)
    parser.add_argument("--backup-reference", required=True)
    parser.add_argument("--rollback-reference", required=True)
    parser.add_argument("--timezone", default="America/Chicago")
    parser.add_argument("--http-timeout", type=int, default=10)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reverse-proxy-https-wss", action="store_true")
    parser.add_argument("--backup-created", action="store_true")
    parser.add_argument("--restore-rehearsed", action="store_true")
    parser.add_argument("--rollback-recorded", action="store_true")
    parser.add_argument("--monitoring-verified", action="store_true")
    parser.add_argument("--logs-reviewed-for-sensitive-data", action="store_true")
    parser.add_argument("--netbird-path-verified", action="store_true")
    return parser.parse_args()


def collect(args: argparse.Namespace) -> dict[str, Any]:
    repository_root = args.repository_root.resolve()
    env_file = args.env_file.resolve()

    if not DIGEST_RE.fullmatch(args.expected_manifest_digest):
        fail("expected-manifest-digest must be sha256:<64 lowercase hex characters>")
    if args.http_timeout <= 0:
        fail("http-timeout must be greater than zero")

    previous_image = validate_previous_image(args.previous_known_good_image)
    backup_reference = validate_reference("backup-reference", args.backup_reference)
    rollback_reference = validate_reference("rollback-reference", args.rollback_reference)

    manual_values = {name: bool(getattr(args, name)) for name in REQUIRED_MANUAL_FLAGS}
    missing_attestations = [name for name, value in manual_values.items() if not value]
    if missing_attestations:
        fail("missing required operator attestations: " + ", ".join(sorted(missing_attestations)))

    production_env = parse_env_file(env_file)
    configured_goreevault_image = production_env.get("GOREVAULT_IMAGE", "").strip()
    configured_postgres_image = production_env.get("POSTGRES_IMAGE", "").strip()
    if not image_is_digest_pinned(configured_goreevault_image):
        fail("GOREVAULT_IMAGE in the production environment file is not digest-pinned")
    if not configured_goreevault_image.endswith(f"@{args.expected_manifest_digest}"):
        fail("GOREVAULT_IMAGE does not match the expected RC manifest digest")
    if not image_is_digest_pinned(configured_postgres_image):
        fail("POSTGRES_IMAGE in the production environment file is not digest-pinned")

    verify_contract(repository_root)
    verify_compose_renders(repository_root, env_file, args.compose_file)

    server = inspect_container(args.goreevault_container)
    postgres = inspect_container(args.postgres_container)

    live_goreevault_image = str(server.get("Config", {}).get("Image") or "")
    live_postgres_image = str(postgres.get("Config", {}).get("Image") or "")
    if live_goreevault_image != configured_goreevault_image:
        fail("live GoreeVault container image does not match GOREVAULT_IMAGE")
    if live_postgres_image != configured_postgres_image:
        fail("live PostgreSQL container image does not match POSTGRES_IMAGE")

    verify_https_origin(args.origin, args.http_timeout)

    observed = {
        "backend_loopback_only": backend_is_loopback_only(server),
        "postgres_internal_only": postgres_is_internal_only(postgres),
        "server_non_root": server_is_non_root(server),
        "read_only_root_filesystem": root_filesystem_is_read_only(server),
        "capabilities_dropped": capabilities_are_dropped(server),
        "no_new_privileges": no_new_privileges_enabled(server),
        "registration_closed": registration_is_closed(server),
        "admin_disabled": admin_is_disabled(server),
        "immutable_digests": (
            image_is_digest_pinned(live_goreevault_image)
            and image_is_digest_pinned(live_postgres_image)
            and live_goreevault_image.endswith(f"@{args.expected_manifest_digest}")
        ),
    }
    failed_observations = [name for name, value in observed.items() if not value]
    if failed_observations:
        fail("target environment failed observed controls: " + ", ".join(sorted(failed_observations)))

    try:
        tested_at = datetime.now(ZoneInfo(args.timezone)).isoformat(timespec="seconds")
    except Exception as exc:
        fail(f"invalid or unavailable timezone: {args.timezone}")
        raise AssertionError from exc

    return {
        "result": "pass",
        "origin": args.origin,
        "tested_at": tested_at,
        "backend_loopback_only": True,
        "reverse_proxy_https_wss": True,
        "postgres_internal_only": True,
        "server_non_root": True,
        "read_only_root_filesystem": True,
        "capabilities_dropped": True,
        "no_new_privileges": True,
        "registration_closed": True,
        "admin_disabled": True,
        "backup_created": True,
        "restore_rehearsed": True,
        "rollback_recorded": True,
        "immutable_digests": True,
        "monitoring_verified": True,
        "logs_reviewed_for_sensitive_data": True,
        "netbird_path_verified": True,
        "goreevault_image": live_goreevault_image,
        "previous_known_good_image": previous_image,
        "backup_reference": backup_reference,
        "rollback_reference": rollback_reference,
    }


def main() -> int:
    args = parse_args()
    try:
        evidence = collect(args)
    except EvidenceError as exc:
        print(f"target evidence collection failed: {exc}", file=sys.stderr)
        return 1

    encoded = json.dumps(evidence, indent=2, sort_keys=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
        print(f"wrote target-environment evidence to {args.output}")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
