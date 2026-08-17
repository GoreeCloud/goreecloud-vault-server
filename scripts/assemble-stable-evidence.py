#!/usr/bin/env python3
"""Assemble and validate GoreeVault Stable evidence from reviewed JSON sections.

The assembler does not create evidence or mark work complete. It combines section
files produced after real validation, binds them to an exact RC, runs the same
fail-closed Stable validator used by release promotion, and writes a mode-0600
canonical evidence file only after validation succeeds.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SECTION_ARGUMENTS = (
    ("rc", "rc"),
    ("multi_user", "multi-user"),
    ("clients", "clients"),
    ("webauthn", "webauthn"),
    ("glaze_ui", "glaze-ui"),
    ("target_environment", "target-environment"),
    ("governance", "governance"),
    ("approvals", "approvals"),
)


class AssemblyError(ValueError):
    pass


def load_validator() -> ModuleType:
    path = ROOT / "scripts" / "validate-stable-evidence.py"
    spec = importlib.util.spec_from_file_location("goreevault_stable_evidence", path)
    if spec is None or spec.loader is None:
        raise AssemblyError("cannot load scripts/validate-stable-evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_section(path: Path, validator: ModuleType) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AssemblyError(f"cannot read evidence section {path}: {exc}") from exc
    try:
        return validator.load_json_strict(raw)
    except (json.JSONDecodeError, validator.EvidenceError) as exc:
        raise AssemblyError(f"invalid evidence section {path}: {exc}") from exc


def collected_at(value: str | None, timezone: str) -> str:
    if value is not None:
        return value
    try:
        return datetime.now(ZoneInfo(timezone)).isoformat(timespec="seconds")
    except Exception as exc:
        raise AssemblyError(f"invalid or unavailable timezone: {timezone}") from exc


def assemble(
    sections: dict[str, Any],
    *,
    assembled_at: str,
    expected_source_sha: str,
    expected_rc_tag: str,
    expected_manifest_digest: str,
    validator: ModuleType,
) -> dict[str, Any]:
    missing = [key for key, _ in SECTION_ARGUMENTS if key not in sections]
    if missing:
        raise AssemblyError("missing evidence sections: " + ", ".join(missing))

    evidence: dict[str, Any] = {
        "schema_version": 2,
        "collected_at": assembled_at,
        "rc": sections["rc"],
        "multi_user": sections["multi_user"],
        "clients": sections["clients"],
        "webauthn": sections["webauthn"],
        "glaze_ui": sections["glaze_ui"],
        "target_environment": sections["target_environment"],
        "governance": sections["governance"],
        "approvals": sections["approvals"],
    }

    try:
        validator.validate_evidence(
            evidence,
            expected_source_sha=expected_source_sha,
            expected_rc_tag=expected_rc_tag,
            expected_manifest_digest=expected_manifest_digest,
            allow_placeholders=False,
        )
    except validator.EvidenceError as exc:
        raise AssemblyError(f"assembled Stable evidence is invalid: {exc}") from exc

    return evidence


def write_evidence(path: Path, evidence: dict[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise AssemblyError(f"output already exists; refuse to overwrite without --force: {path}")
    if path.is_symlink():
        raise AssemblyError(f"refuse to write Stable evidence through a symbolic link: {path}")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if not force:
            flags |= os.O_EXCL
        descriptor = os.open(path, flags, 0o600)
        try:
            payload = json.dumps(evidence, indent=2, sort_keys=False) + "\n"
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        path.chmod(0o600)
    except OSError as exc:
        raise AssemblyError(f"cannot write Stable evidence {path}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for _, option in SECTION_ARGUMENTS:
        parser.add_argument(f"--{option}", required=True, type=Path)
    parser.add_argument("--expected-source-sha", required=True)
    parser.add_argument("--expected-rc-tag", required=True)
    parser.add_argument("--expected-manifest-digest", required=True)
    parser.add_argument("--collected-at")
    parser.add_argument("--timezone", default="America/Chicago")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Explicitly replace an existing ordinary output file after validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validator = load_validator()

    try:
        sections: dict[str, Any] = {}
        for key, option in SECTION_ARGUMENTS:
            sections[key] = read_section(getattr(args, option.replace("-", "_")), validator)

        evidence = assemble(
            sections,
            assembled_at=collected_at(args.collected_at, args.timezone),
            expected_source_sha=args.expected_source_sha,
            expected_rc_tag=args.expected_rc_tag,
            expected_manifest_digest=args.expected_manifest_digest,
            validator=validator,
        )
        write_evidence(args.output, evidence, force=args.force)
    except AssemblyError as exc:
        print(f"Stable evidence assembly failed: {exc}", file=sys.stderr)
        return 1

    print(f"Validated Stable evidence written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
