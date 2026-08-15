#!/usr/bin/env python3
"""Validate GoreeVault evidence tooling, client/RC records, and Web contract."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/CLIENT-COMPATIBILITY.md",
    "docs/RC-EVIDENCE.md",
    "docs/WEB-CLIENT-CONTRACT.md",
    "scripts/collect-target-evidence.py",
    "scripts/validate-stable-evidence.py",
    "tests/test_collect_target_evidence.py",
)


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_stable_validator() -> ModuleType:
    path = ROOT / "scripts" / "validate-stable-evidence.py"
    spec = importlib.util.spec_from_file_location("goreevault_stable_evidence", path)
    require(spec is not None and spec.loader is not None, "cannot load Stable evidence validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def client_section(text: str, kind: str) -> str:
    marker = f"`kind: {kind}`"
    marker_index = text.find(marker)
    require(marker_index >= 0, f"client compatibility matrix is missing required kind: {kind}")
    section_start = text.rfind("\n## ", 0, marker_index)
    if section_start < 0:
        section_start = 0
    else:
        section_start += 1
    next_section = text.find("\n## ", marker_index)
    if next_section < 0:
        next_section = len(text)
    return text[section_start:next_section]


def validate_client_matrix(stable: ModuleType) -> None:
    required_kinds = set(stable.REQUIRED_CLIENT_KINDS)
    required_checks = set(stable.REQUIRED_CLIENT_CHECKS)
    text = read("docs/CLIENT-COMPATIBILITY.md")

    require(
        "aligned to Stable-evidence schema version 2" in text,
        "client compatibility matrix must declare alignment with Stable evidence schema v2",
    )
    require(
        "N/A`, `FAIL`, and `NOT TESTED` do **not** satisfy" in text,
        "client compatibility matrix must state the schema-v2 fail-closed result rule",
    )

    for kind in sorted(required_kinds):
        section = client_section(text, kind)
        missing = sorted(check for check in required_checks if f"`{check}`" not in section)
        require(
            not missing,
            f"client compatibility section {kind} is missing Stable evidence checks: {', '.join(missing)}",
        )

    webauthn_section_start = text.find("## Real WebAuthn/passkey evidence")
    require(webauthn_section_start >= 0, "client compatibility matrix is missing real WebAuthn evidence")
    webauthn_section = text[webauthn_section_start:]
    for field in ("`webauthn.registration`", "`webauthn.authentication`"):
        require(field in webauthn_section, f"client compatibility matrix is missing {field}")

    require(
        "scripts/validate-stable-evidence.py" in text,
        "client compatibility matrix must direct final evidence through the Stable validator",
    )


def validate_rc_evidence(stable: ModuleType) -> None:
    text = read("docs/RC-EVIDENCE.md")
    required_sections = (
        "## Candidate identity",
        "## Repository release controls",
        "## Automated exact-head source gates",
        "## Automated authentication and multi-user regression evidence",
        "## Supply-chain evidence",
        "## Backup, restore, and migration evidence",
        "## Security disposition",
        "## Real multi-user evidence",
        "## Real client and WebAuthn evidence",
        "## Target-environment rehearsal evidence",
        "## Glaze UI evidence",
        "## Open readiness blockers reconciliation",
        "## RC decision",
        "## Stable evidence assembly",
        "## Stable promotion verification",
        "## Final Stable decision",
    )
    missing_sections = [section for section in required_sections if section not in text]
    require(not missing_sections, f"RC evidence record is missing release sections: {', '.join(missing_sections)}")

    for kind in sorted(set(stable.REQUIRED_CLIENT_KINDS)):
        require(
            f"`kind: {kind}`" in text,
            f"RC evidence record is missing required Stable client kind: {kind}",
        )

    required_tokens = (
        "scripts/collect-target-evidence.py",
        "scripts/validate-stable-evidence.py",
        "docs/CLIENT-COMPATIBILITY.md",
        "docs/WEB-CLIENT-CONTRACT.md",
        "GoreeVault Evidence Tooling",
        "GoreeVault Repository Readiness",
        "GoreeVault Stable Evidence self-tests",
        "GoreeVault Glaze UI server-owned surfaces",
        "Primary production browser vault is GoreeCloud-owned: NO",
        "Approval of a server RC does not imply product-wide Stable approval.",
        "Stable workflow downloaded and validated the canonical evidence asset",
    )
    missing = [token for token in required_tokens if token not in text]
    require(not missing, f"RC evidence record is missing current release-contract controls: {', '.join(missing)}")


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
        stable = load_stable_validator()
        validate_collector()
        validate_client_matrix(stable)
        validate_rc_evidence(stable)
        validate_web_contract()
        validate_tests()
    except (OSError, UnicodeError, ValidationError) as exc:
        print(f"Evidence tooling validation failed: {exc}", file=sys.stderr)
        return 1

    print("GoreeVault evidence tooling, client/RC records, and Web client contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
