#!/usr/bin/env python3
"""Validate GoreeVault Stable release evidence.

This validator intentionally uses only the Python standard library so it can run
in GitHub Actions and on an administrator workstation without extra packages.
It is fail-closed: missing, malformed, stale, placeholder, or incomplete
evidence rejects Stable promotion.
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


class EvidenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


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


def require_true_map(mapping: Any, keys: set[str], field: str) -> None:
    require(isinstance(mapping, dict), f"{field} must be an object")
    for key in sorted(keys):
        require(mapping.get(key) is True, f"{field}.{key} must be true")


def parse_timestamp(value: Any, field: str) -> None:
    text = require_nonempty_string(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{field} must be an ISO 8601 timestamp") from exc
    require(parsed.tzinfo is not None, f"{field} must include a timezone offset")


def validate_evidence(
    data: Any,
    *,
    expected_source_sha: str | None,
    expected_rc_tag: str | None,
    expected_manifest_digest: str | None,
    allow_placeholders: bool,
) -> None:
    require(isinstance(data, dict), "evidence root must be a JSON object")
    if not allow_placeholders:
        reject_placeholders(data)

    require(data.get("schema_version") == 2, "schema_version must equal 2")
    parse_timestamp(data.get("collected_at"), "collected_at")

    rc = data.get("rc")
    require(isinstance(rc, dict), "rc must be an object")

    rc_tag = require_nonempty_string(rc.get("tag"), "rc.tag")
    source_sha = require_nonempty_string(rc.get("source_sha"), "rc.source_sha")
    manifest_digest = require_nonempty_string(rc.get("manifest_digest"), "rc.manifest_digest")
    postgres_image = require_nonempty_string(rc.get("postgres_image"), "rc.postgres_image")
    require_nonempty_string(rc.get("browser_vault_asset"), "rc.browser_vault_asset")

    require(RC_TAG_RE.fullmatch(rc_tag) is not None, "rc.tag must be a semantic RC tag such as v0.3.0-rc.1")
    require(SHA_RE.fullmatch(source_sha) is not None, "rc.source_sha must be a lowercase 40-character commit SHA")
    require(
        DIGEST_RE.fullmatch(manifest_digest) is not None,
        "rc.manifest_digest must be a sha256 OCI manifest digest",
    )
    require(
        "@sha256:" in postgres_image,
        "rc.postgres_image must be an immutable image reference containing @sha256:",
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
    require(isinstance(multi_user, dict), "multi_user must be an object")
    require(multi_user.get("result") == "pass", "multi_user.result must equal 'pass'")
    parse_timestamp(multi_user.get("tested_at"), "multi_user.tested_at")
    require_true_map(multi_user, REQUIRED_MULTI_USER_FLAGS, "multi_user")
    require_nonempty_string(multi_user.get("evidence_reference"), "multi_user.evidence_reference")

    clients = data.get("clients")
    require(isinstance(clients, list) and clients, "clients must be a non-empty array")
    seen: set[str] = set()

    for index, client in enumerate(clients):
        field = f"clients[{index}]"
        require(isinstance(client, dict), f"{field} must be an object")
        kind = require_nonempty_string(client.get("kind"), f"{field}.kind")
        require(kind in REQUIRED_CLIENT_KINDS, f"{field}.kind is unsupported: {kind}")
        require(kind not in seen, f"duplicate client evidence for kind: {kind}")
        seen.add(kind)
        require_nonempty_string(client.get("name"), f"{field}.name")
        require_nonempty_string(client.get("platform"), f"{field}.platform")
        require_nonempty_string(client.get("version"), f"{field}.version")
        parse_timestamp(client.get("tested_at"), f"{field}.tested_at")
        require(client.get("result") == "pass", f"{field}.result must equal 'pass'")
        require_true_map(client.get("checks"), REQUIRED_CLIENT_CHECKS, f"{field}.checks")

    missing_clients = sorted(REQUIRED_CLIENT_KINDS - seen)
    require(not missing_clients, f"missing required real-client evidence: {', '.join(missing_clients)}")

    webauthn = data.get("webauthn")
    require(isinstance(webauthn, dict), "webauthn must be an object")
    require(webauthn.get("result") == "pass", "webauthn.result must equal 'pass'")
    require_nonempty_string(webauthn.get("browser"), "webauthn.browser")
    require_nonempty_string(webauthn.get("browser_version"), "webauthn.browser_version")
    require_nonempty_string(webauthn.get("platform"), "webauthn.platform")
    require_nonempty_string(webauthn.get("authenticator"), "webauthn.authenticator")
    parse_timestamp(webauthn.get("tested_at"), "webauthn.tested_at")
    require(webauthn.get("registration") is True, "webauthn.registration must be true")
    require(webauthn.get("authentication") is True, "webauthn.authentication must be true")

    glaze = data.get("glaze_ui")
    require(isinstance(glaze, dict), "glaze_ui must be an object")
    require(glaze.get("result") == "pass", "glaze_ui.result must equal 'pass'")
    parse_timestamp(glaze.get("reviewed_at"), "glaze_ui.reviewed_at")
    require_true_map(glaze, REQUIRED_GLAZE_FLAGS, "glaze_ui")
    require_nonempty_string(glaze.get("evidence_reference"), "glaze_ui.evidence_reference")

    target = data.get("target_environment")
    require(isinstance(target, dict), "target_environment must be an object")
    require(target.get("result") == "pass", "target_environment.result must equal 'pass'")
    require(
        target.get("origin") == "https://vault.goreecloud.com",
        "target_environment.origin must equal https://vault.goreecloud.com",
    )
    parse_timestamp(target.get("tested_at"), "target_environment.tested_at")
    require_true_map(target, REQUIRED_TARGET_FLAGS, "target_environment")
    goreevault_image = require_nonempty_string(target.get("goreevault_image"), "target_environment.goreevault_image")
    require(
        goreevault_image.endswith(manifest_digest),
        "target_environment.goreevault_image must reference the exact RC manifest digest",
    )
    previous_image = require_nonempty_string(
        target.get("previous_known_good_image"),
        "target_environment.previous_known_good_image",
    )
    require("@sha256:" in previous_image, "previous_known_good_image must be digest pinned")
    require_nonempty_string(target.get("backup_reference"), "target_environment.backup_reference")
    require_nonempty_string(target.get("rollback_reference"), "target_environment.rollback_reference")

    governance = data.get("governance")
    require(isinstance(governance, dict), "governance must be an object")
    parse_timestamp(governance.get("verified_at"), "governance.verified_at")
    require_true_map(governance, REQUIRED_GOVERNANCE_FLAGS, "governance")
    for key in sorted(CONDITIONAL_GOVERNANCE_CONTROLS):
        state = governance.get(key)
        require(
            state in ALLOWED_CONDITIONAL_STATES,
            f"governance.{key} must be one of: {', '.join(sorted(ALLOWED_CONDITIONAL_STATES))}",
        )

    approvals = data.get("approvals")
    require(isinstance(approvals, list) and approvals, "approvals must contain at least one reviewer record")
    for index, approval in enumerate(approvals):
        field = f"approvals[{index}]"
        require(isinstance(approval, dict), f"{field} must be an object")
        require_nonempty_string(approval.get("reviewer"), f"{field}.reviewer")
        parse_timestamp(approval.get("reviewed_at"), f"{field}.reviewed_at")
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
        data = json.loads(raw)
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
