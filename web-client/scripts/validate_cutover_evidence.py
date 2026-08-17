#!/usr/bin/env python3
"""Validate GoreeVault Web browser cutover and rollback evidence."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OCI_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PLACEHOLDERS = {"", "tbd", "todo", "pending", "unset", "unknown", "n/a"}

ROOT_FIELDS = {
    "schema",
    "product",
    "status",
    "previousClient",
    "candidate",
    "server",
    "evidence",
    "rollback",
    "operator",
    "outcome",
}


def require_object(value: Any, field: str, allowed_fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    extras = set(value) - allowed_fields
    missing = allowed_fields - set(value)
    if extras:
        raise ValueError(f"{field} contains unsupported fields: {', '.join(sorted(extras))}")
    if missing:
        raise ValueError(f"{field} is missing fields: {', '.join(sorted(missing))}")
    return value


def require_string(value: Any, field: str, *, final: bool) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if final and normalized.lower() in PLACEHOLDERS:
        raise ValueError(f"{field} must not contain a placeholder in final evidence")
    return normalized


def require_pattern(value: Any, field: str, pattern: re.Pattern[str], *, final: bool) -> str:
    normalized = require_string(value, field, final=final)
    if final and not pattern.fullmatch(normalized):
        raise ValueError(f"{field} has an invalid immutable identity")
    return normalized


def require_timezone_timestamp(value: Any, field: str, *, final: bool) -> str:
    normalized = require_string(value, field, final=final)
    if not final:
        return normalized
    candidate = normalized[:-1] + "+00:00" if normalized.endswith("Z") else normalized
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return normalized


def validate_record(record: Any, *, allow_template: bool = False) -> dict[str, Any]:
    root = require_object(record, "record", ROOT_FIELDS)
    if root["schema"] != 1:
        raise ValueError("schema must be 1")
    if root["product"] != "GoreeVault Web":
        raise ValueError("product must be GoreeVault Web")

    status = require_string(root["status"], "status", final=False)
    if status not in {"template", "final"}:
        raise ValueError("status must be template or final")
    if status == "template" and not allow_template:
        raise ValueError("template evidence cannot satisfy cutover validation")
    final = status == "final"

    previous = require_object(
        root["previousClient"],
        "previousClient",
        {"name", "version", "artifactIdentity"},
    )
    require_string(previous["name"], "previousClient.name", final=final)
    require_string(previous["version"], "previousClient.version", final=final)
    require_string(previous["artifactIdentity"], "previousClient.artifactIdentity", final=final)

    candidate = require_object(
        root["candidate"],
        "candidate",
        {"sourceRevision", "artifactSha256", "releaseManifestSha256", "sbomSha256"},
    )
    require_pattern(candidate["sourceRevision"], "candidate.sourceRevision", GIT_SHA_RE, final=final)
    require_pattern(candidate["artifactSha256"], "candidate.artifactSha256", SHA256_RE, final=final)
    require_pattern(
        candidate["releaseManifestSha256"],
        "candidate.releaseManifestSha256",
        SHA256_RE,
        final=final,
    )
    require_pattern(candidate["sbomSha256"], "candidate.sbomSha256", SHA256_RE, final=final)

    server = require_object(root["server"], "server", {"sourceRevision", "ociManifestDigest"})
    require_pattern(server["sourceRevision"], "server.sourceRevision", GIT_SHA_RE, final=final)
    require_pattern(server["ociManifestDigest"], "server.ociManifestDigest", OCI_SHA256_RE, final=final)

    evidence = require_object(
        root["evidence"],
        "evidence",
        {"compatibility", "accessibility", "security", "rollback"},
    )
    for key in sorted(evidence):
        require_string(evidence[key], f"evidence.{key}", final=final)

    rollback = require_object(
        root["rollback"],
        "rollback",
        {"procedure", "requiresDatabaseDowngrade", "requiresPlaintextExport"},
    )
    require_string(rollback["procedure"], "rollback.procedure", final=final)
    if rollback["requiresDatabaseDowngrade"] is not False:
        raise ValueError("rollback must not require a database downgrade")
    if rollback["requiresPlaintextExport"] is not False:
        raise ValueError("rollback must not require plaintext export")

    operator = require_object(root["operator"], "operator", {"name", "timestamp"})
    require_string(operator["name"], "operator.name", final=final)
    require_timezone_timestamp(operator["timestamp"], "operator.timestamp", final=final)

    outcome = require_string(root["outcome"], "outcome", final=False)
    if final and outcome not in {"accepted", "rolled-back", "failed"}:
        raise ValueError("final outcome must be accepted, rolled-back, or failed")
    if not final and outcome != "pending":
        raise ValueError("template outcome must be pending")

    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument(
        "--allow-template",
        action="store_true",
        help="Validate template structure without treating it as cutover-ready final evidence.",
    )
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    validate_record(record, allow_template=args.allow_template)
    mode = "template" if record["status"] == "template" else "final"
    print(f"Validated GoreeVault Web {mode} cutover evidence: {args.record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
