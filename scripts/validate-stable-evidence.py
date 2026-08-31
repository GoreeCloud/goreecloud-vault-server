#!/usr/bin/env python3
"""Validate GoreeVault Stable release evidence.

This validator intentionally uses only the Python standard library so it can run
in GitHub Actions and on an administrator workstation without extra packages.
It is fail-closed: missing, malformed, ambiguous, placeholder, unknown, or
incomplete evidence rejects Stable promotion.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
IMMUTABLE_REF_RE = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
RC_TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+-rc\.[0-9]+$")
PLACEHOLDER_TOKEN = "REPLACE_ME"

REQUIRED_CLIENT_KINDS = {
    "web",
    "chromium_extension",
    "firefox_extension",
    "desktop",
    "android",
    "cli",
}

REQUIRED_CLIENT_CHECKS = {
    "sign_in_unlock",
    "full_sync",
    "create_update_delete",
    "attachments",
    "organization_collections",
    "totp",
    "refresh_rotation_replay",
    "logout_session_invalidation",
}

REQUIRED_MULTI_USER_FLAGS = {
    "individual_accounts",
    "private_vault_isolation",
    "unrelated_user_access_denied",
    "organization_membership_boundaries",
    "collection_authorization",
    "permission_change_enforced",
    "member_removal_enforced",
    "session_device_invalidation",
    "no_shared_admin_required",
}

REQUIRED_GLAZE_FLAGS = {
    "product_wide_conformance",
    "primary_browser_vault_goreecloud_owned",
    "controlled_surfaces_glaze",
    "system_light_dark",
    "keyboard_accessibility",
    "reduced_motion",
    "increased_contrast",
    "forced_colors",
    "local_only_presentation_dependencies",
    "no_analytics_tracking",
}

REQUIRED_TARGET_FLAGS = {
    "backend_loopback_only",
    "reverse_proxy_https_wss",
    "postgres_internal_only",
    "server_non_root",
    "read_only_root_filesystem",
    "capabilities_dropped",
    "no_new_privileges",
    "registration_closed",
    "admin_disabled",
    "backup_created",
    "restore_rehearsed",
    "rollback_recorded",
    "immutable_digests",
    "monitoring_verified",
    "logs_reviewed_for_sensitive_data",
    "netbird_path_verified",
}

REQUIRED_GOVERNANCE_FLAGS = {
    "main_protected",
    "required_checks_enforced",
    "codeowners_review_enforced",
    "release_environment_protected",
    "release_reviewer_required",
    "release_self_review_prevented",
    "actions_default_read_only",
    "dependabot_alerts_enabled",
}

CONDITIONAL_GOVERNANCE_CONTROLS = {
    "secret_scanning",
    "push_protection",
    "private_vulnerability_reporting",
}

ALLOWED_CONDITIONAL_STATES = {"pass", "not_supported"}

ROOT_KEYS = {
    "schema_version",
    "collected_at",
    "rc",
    "multi_user",
    "clients",
    "webauthn",
    "glaze_ui",
    "target_environment",
    "governance",
    "approvals",
}
RC_KEYS = {"tag", "source_sha", "manifest_digest", "postgres_image", "browser_vault_asset"}
MULTI_USER_KEYS = {"result", "tested_at", "evidence_reference"} | REQUIRED_MULTI_USER_FLAGS
CLIENT_KEYS = {"kind", "name", "platform", "version", "tested_at", "result", "checks"}
WEBAUTHN_KEYS = {
    "result",
    "browser",
    "browser_version",
    "platform",
    "authenticator",
    "tested_at",
    "registration",
    "authentication",
}
GLAZE_KEYS = {"result", "reviewed_at", "evidence_reference"} | REQUIRED_GLAZE_FLAGS
TARGET_KEYS = {
    "result",
    "origin",
    "tested_at",
    "goreevault_image",
    "previous_known_good_image",
    "backup_reference",
    "rollback_reference",
} | REQUIRED_TARGET_FLAGS
GOVERNANCE_KEYS = {"verified_at"} | REQUIRED_GOVERNANCE_FLAGS | CONDITIONAL_GOVERNANCE_CONTROLS
APPROVAL_KEYS = {"reviewer", "reviewed_at", "result"}


class EvidenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def strict_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting duplicate keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key is not allowed: {key}")
        result[key] = value
    return result


def load_json_strict(raw: str) -> Any:
    return json.loads(raw, object_pairs_hook=strict_object_pairs)


def require_exact_keys(mapping: Any, expected: set[str], field: str) -> None:
    require(isinstance(mapping, dict), f"{field} must be an object")
    actual = set(mapping)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    require(not missing, f"{field} is missing required fields: {', '.join(missing)}")
    require(not extra, f"{field} contains unknown fields: {', '.join(extra)}")


def reject_placeholders(value: Any, field: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            reject_placeholders(child, f"{field}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_placeholders(child, f"{field}[{index}]")
    elif isinstance(value, str):
        require(PLACEHOLDER_TOKEN not in value, f"{field} still contains a template placeholder")


def require_nonempty_string(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip() != "", f"{field} must be a non-empty string")
    return value.strip()


def require_immutable_reference(value: Any, field: str) -> str:
    text = require_nonempty_string(value, field)
    require(
        IMMUTABLE_REF_RE.fullmatch(text) is not None,
        f"{field} must be an immutable name@sha256:<64 lowercase hex> reference",
    )
    return text


def immutable_reference_digest(reference: str) -> str:
    return reference.rsplit("@", 1)[1]


def require_true_fields(mapping: dict[str, Any], keys: set[str], field: str) -> None:
    for key in sorted(keys):
        require(mapping.get(key) is True, f"{field}.{key} must be true")


def parse_timestamp(value: Any, field: str) -> datetime:
    text = require_nonempty_string(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{field} must be an ISO 8601 timestamp") from exc
    require(parsed.tzinfo is not None, f"{field} must include a timezone offset")
    return parsed


def require_timestamp_at_or_before(
    value: Any,
    field: str,
    ceiling: datetime,
    ceiling_field: str,
) -> datetime:
    parsed = parse_timestamp(value, field)
    require(parsed <= ceiling, f"{field} cannot be after {ceiling_field}")
    return parsed


def validate_evidence(
    data: Any,
    *,
    expected_source_sha: str | None,
    expected_rc_tag: str | None,
    expected_manifest_digest: str | None,
    allow_placeholders: bool,
) -> None:
    require_exact_keys(data, ROOT_KEYS, "root")
    if not allow_placeholders:
        reject_placeholders(data)

    require(data.get("schema_version") == 2, "schema_version must equal 2")
    collected_at = parse_timestamp(data.get("collected_at"), "collected_at")
    evidence_timestamps: list[datetime] = []

    rc = data.get("rc")
    require_exact_keys(rc, RC_KEYS, "rc")
    assert isinstance(rc, dict)

    rc_tag = require_nonempty_string(rc.get("tag"), "rc.tag")
    source_sha = require_nonempty_string(rc.get("source_sha"), "rc.source_sha")
    manifest_digest = require_nonempty_string(rc.get("manifest_digest"), "rc.manifest_digest")
    postgres_image = require_immutable_reference(rc.get("postgres_image"), "rc.postgres_image")
    browser_vault_asset = require_immutable_reference(rc.get("browser_vault_asset"), "rc.browser_vault_asset")

    require(RC_TAG_RE.fullmatch(rc_tag) is not None, "rc.tag must be a semantic RC tag such as v0.3.0-rc.1")
    require(SHA_RE.fullmatch(source_sha) is not None, "rc.source_sha must be a lowercase 40-character commit SHA")
    require(
        DIGEST_RE.fullmatch(manifest_digest) is not None,
        "rc.manifest_digest must be a sha256 OCI manifest digest",
    )
    require(
        immutable_reference_digest(postgres_image) != manifest_digest,
        "rc.postgres_image must identify the PostgreSQL artifact rather than reuse the GoreeVault manifest digest",
    )
    require(
        immutable_reference_digest(browser_vault_asset) != manifest_digest,
        "rc.browser_vault_asset must have its own immutable asset digest rather than reuse the server manifest digest",
    )

    if expected_source_sha is not None:
        require(source_sha == expected_source_sha, "rc.source_sha does not match the Stable source SHA")
    if expected_rc_tag is not None:
        require(rc_tag == expected_rc_tag, "rc.tag does not match the RC selected for Stable promotion")
    if expected_manifest_digest is not None:
        require(
            manifest_digest == expected_manifest_digest,
            "rc.manifest_digest does not match the exact RC OCI manifest selected for Stable promotion",
        )

    multi_user = data.get("multi_user")
    require_exact_keys(multi_user, MULTI_USER_KEYS, "multi_user")
    assert isinstance(multi_user, dict)
    require(multi_user.get("result") == "pass", "multi_user.result must equal 'pass'")
    evidence_timestamps.append(
        require_timestamp_at_or_before(
            multi_user.get("tested_at"), "multi_user.tested_at", collected_at, "collected_at"
        )
    )
    require_true_fields(multi_user, REQUIRED_MULTI_USER_FLAGS, "multi_user")
    require_nonempty_string(multi_user.get("evidence_reference"), "multi_user.evidence_reference")

    clients = data.get("clients")
    require(isinstance(clients, list) and clients, "clients must be a non-empty array")
    seen: set[str] = set()

    for index, client in enumerate(clients):
        field = f"clients[{index}]"
        require_exact_keys(client, CLIENT_KEYS, field)
        assert isinstance(client, dict)
        kind = require_nonempty_string(client.get("kind"), f"{field}.kind")
        require(kind in REQUIRED_CLIENT_KINDS, f"{field}.kind is unsupported: {kind}")
        require(kind not in seen, f"duplicate client evidence for kind: {kind}")
        seen.add(kind)
        require_nonempty_string(client.get("name"), f"{field}.name")
        require_nonempty_string(client.get("platform"), f"{field}.platform")
        require_nonempty_string(client.get("version"), f"{field}.version")
        evidence_timestamps.append(
            require_timestamp_at_or_before(
                client.get("tested_at"), f"{field}.tested_at", collected_at, "collected_at"
            )
        )
        require(client.get("result") == "pass", f"{field}.result must equal 'pass'")
        checks = client.get("checks")
        require_exact_keys(checks, REQUIRED_CLIENT_CHECKS, f"{field}.checks")
        assert isinstance(checks, dict)
        require_true_fields(checks, REQUIRED_CLIENT_CHECKS, f"{field}.checks")

    missing_clients = sorted(REQUIRED_CLIENT_KINDS - seen)
    require(not missing_clients, f"missing required real-client evidence: {', '.join(missing_clients)}")

    webauthn = data.get("webauthn")
    require_exact_keys(webauthn, WEBAUTHN_KEYS, "webauthn")
    assert isinstance(webauthn, dict)
    require(webauthn.get("result") == "pass", "webauthn.result must equal 'pass'")
    require_nonempty_string(webauthn.get("browser"), "webauthn.browser")
    require_nonempty_string(webauthn.get("browser_version"), "webauthn.browser_version")
    require_nonempty_string(webauthn.get("platform"), "webauthn.platform")
    require_nonempty_string(webauthn.get("authenticator"), "webauthn.authenticator")
    evidence_timestamps.append(
        require_timestamp_at_or_before(
            webauthn.get("tested_at"), "webauthn.tested_at", collected_at, "collected_at"
        )
    )
    require(webauthn.get("registration") is True, "webauthn.registration must be true")
    require(webauthn.get("authentication") is True, "webauthn.authentication must be true")

    glaze = data.get("glaze_ui")
    require_exact_keys(glaze, GLAZE_KEYS, "glaze_ui")
    assert isinstance(glaze, dict)
    require(glaze.get("result") == "pass", "glaze_ui.result must equal 'pass'")
    evidence_timestamps.append(
        require_timestamp_at_or_before(
            glaze.get("reviewed_at"), "glaze_ui.reviewed_at", collected_at, "collected_at"
        )
    )
    require_true_fields(glaze, REQUIRED_GLAZE_FLAGS, "glaze_ui")
    require_nonempty_string(glaze.get("evidence_reference"), "glaze_ui.evidence_reference")

    target = data.get("target_environment")
    require_exact_keys(target, TARGET_KEYS, "target_environment")
    assert isinstance(target, dict)
    require(target.get("result") == "pass", "target_environment.result must equal 'pass'")
    require(
        target.get("origin") == "https://vault.goreecloud.com",
        "target_environment.origin must equal https://vault.goreecloud.com",
    )
    evidence_timestamps.append(
        require_timestamp_at_or_before(
            target.get("tested_at"), "target_environment.tested_at", collected_at, "collected_at"
        )
    )
    require_true_fields(target, REQUIRED_TARGET_FLAGS, "target_environment")
    goreevault_image = require_immutable_reference(
        target.get("goreevault_image"),
        "target_environment.goreevault_image",
    )
    require(
        immutable_reference_digest(goreevault_image) == manifest_digest,
        "target_environment.goreevault_image must reference the exact RC manifest digest",
    )
    previous_image = require_immutable_reference(
        target.get("previous_known_good_image"),
        "target_environment.previous_known_good_image",
    )
    require(
        immutable_reference_digest(previous_image) != manifest_digest,
        "previous_known_good_image must identify a distinct previously accepted artifact",
    )
    require_nonempty_string(target.get("backup_reference"), "target_environment.backup_reference")
    require_nonempty_string(target.get("rollback_reference"), "target_environment.rollback_reference")

    governance = data.get("governance")
    require_exact_keys(governance, GOVERNANCE_KEYS, "governance")
    assert isinstance(governance, dict)
    evidence_timestamps.append(
        require_timestamp_at_or_before(
            governance.get("verified_at"), "governance.verified_at", collected_at, "collected_at"
        )
    )
    require_true_fields(governance, REQUIRED_GOVERNANCE_FLAGS, "governance")
    for key in sorted(CONDITIONAL_GOVERNANCE_CONTROLS):
        state = governance.get(key)
        require(
            state in ALLOWED_CONDITIONAL_STATES,
            f"governance.{key} must be one of: {', '.join(sorted(ALLOWED_CONDITIONAL_STATES))}",
        )

    latest_evidence_at = max(evidence_timestamps)
    approvals = data.get("approvals")
    require(isinstance(approvals, list) and approvals, "approvals must contain at least one reviewer record")
    seen_reviewers: set[str] = set()
    for index, approval in enumerate(approvals):
        field = f"approvals[{index}]"
        require_exact_keys(approval, APPROVAL_KEYS, field)
        assert isinstance(approval, dict)
        reviewer = require_nonempty_string(approval.get("reviewer"), f"{field}.reviewer")
        reviewer_identity = reviewer.casefold()
        require(
            reviewer_identity not in seen_reviewers,
            f"duplicate approval reviewer is not allowed: {reviewer}",
        )
        seen_reviewers.add(reviewer_identity)
        reviewed_at = require_timestamp_at_or_before(
            approval.get("reviewed_at"), f"{field}.reviewed_at", collected_at, "collected_at"
        )
        require(
            reviewed_at >= latest_evidence_at,
            f"{field}.reviewed_at cannot be before the latest non-approval evidence",
        )
        require(approval.get("result") == "approved", f"{field}.result must equal 'approved'")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="Path to goreevault-stable-evidence.json")
    parser.add_argument("--expected-source-sha")
    parser.add_argument("--expected-rc-tag")
    parser.add_argument("--expected-manifest-digest")
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow REPLACE_ME template values; intended only for repository self-tests.",
    )
    args = parser.parse_args()

    try:
        raw = args.evidence.read_text(encoding="utf-8")
        data = load_json_strict(raw)
        validate_evidence(
            data,
            expected_source_sha=args.expected_source_sha,
            expected_rc_tag=args.expected_rc_tag,
            expected_manifest_digest=args.expected_manifest_digest,
            allow_placeholders=args.allow_placeholders,
        )
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(f"Stable evidence validation failed: {exc}", file=sys.stderr)
        return 1

    print("Stable evidence validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
