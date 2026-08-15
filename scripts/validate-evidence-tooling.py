#!/usr/bin/env python3
"""Validate GoreeVault target-evidence tooling and GoreeVault Web contract."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/WEB-CLIENT-CONTRACT.md",
    "scripts/collect-target-evidence.py",
    "tests/test_collect_target_evidence.py",
)


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def validate_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    require(not missing, f"missing required evidence/client-contract files: {', '.join(missing)}")


def validate_collector() -> None:
    text = read("scripts/collect-target-evidence.py")
    required_tokens = (
        'EXPECTED_ORIGIN = "https://vault.goreecloud.com"',
        'default="goreevault-server"',
        'default="goreevault-postgres"',
        'mode & 0o077',
        'GOREVAULT_IMAGE',
        'POSTGRES_IMAGE',
        'container_is_running',
        'container_is_healthy',
        'backend_loopback_only',
        'postgres_internal_only',
        'server_non_root',
        'read_only_root_filesystem',
        'capabilities_dropped',
        'no_new_privileges',
        'registration_closed',
        'admin_disabled',
        'logs_reviewed_for_sensitive_data',
        'netbird_path_verified',
        'previous-known-good-image',
        'backup-reference',
        'rollback-reference',
        'docker", "inspect"',
        'curl',
        'args.output.chmod(0o600)',
    )
    missing = [token for token in required_tokens if token not in text]
    require(not missing, f"target evidence collector is missing fail-closed controls: {', '.join(missing)}")
    require(
        "never serializes" in text.lower(),
        "target evidence collector must explicitly prohibit secret serialization",
    )
    require(
        '"target_environment"' not in text,
        "collector must emit the target-environment section itself, not a misleading full Stable evidence record",
    )


def validate_web_contract() -> None:
    text = read("docs/WEB-CLIENT-CONTRACT.md")
    required_phrases = (
        "Role and Purpose",
        "GoreeVault Web must never become a server-side decryption layer",
        "Do not invent cryptographic primitives",
        "GoreeVault Web is a multi-user application",
        "no plaintext vault items",
        "Glaze UI Design Language",
        "no analytics, behavioral tracking",
        "Content Security Policy",
        "Accessibility acceptance",
        "Migration and fallback",
        "Stable-release gate",
        "Starting GoreeVault Web development, creating a repository, or rendering a Glaze UI shell does not close the blocker by itself.",
    )
    missing = [phrase for phrase in required_phrases if phrase not in text]
    require(not missing, f"GoreeVault Web contract is missing required security/readiness language: {', '.join(missing)}")


def validate_tests() -> None:
    text = read("tests/test_collect_target_evidence.py")
    required_tests = (
        "test_digest_pinning",
        "test_container_state_requires_running_and_healthy",
        "test_backend_requires_loopback_publication",
        "test_postgres_must_not_publish_host_port",
        "test_runtime_hardening_checks",
        "test_env_file_rejects_group_or_world_access",
        "test_references_reject_placeholders_and_multiline_values",
        "test_collect_builds_exact_non_secret_target_environment_section",
        "test_collect_rejects_missing_operator_attestation",
        "test_collect_rejects_wrong_rc_manifest",
    )
    missing = [name for name in required_tests if name not in text]
    require(not missing, f"target evidence collector tests are incomplete: {', '.join(missing)}")


def main() -> int:
    try:
        validate_files()
        validate_collector()
        validate_web_contract()
        validate_tests()
    except (OSError, UnicodeError, ValidationError) as exc:
        print(f"Evidence tooling validation failed: {exc}", file=sys.stderr)
        return 1

    print("GoreeVault evidence tooling and Web client contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
