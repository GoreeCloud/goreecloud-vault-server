#!/usr/bin/env python3
"""Validate security invariants for GoreeVault-owned GitHub Actions workflows.

The validator intentionally uses only the Python standard library. It limits its
scope to .github/workflows/goreevault-*.yml so inherited upstream workflows are
not silently reclassified as GoreeVault-owned policy surfaces.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)\s*(?:#.*)?$")
CHECKOUT_RE = re.compile(r"^actions/checkout@([0-9a-f]{40})$")
TOP_LEVEL_PERMISSIONS_RE = re.compile(
    r"^permissions:\s*(?:\{\}|read-all|write-all)?\s*(?:#.*)?$"
)


def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def checkout_block(lines: list[str], index: int) -> list[str]:
    """Return only the current checkout step, never a later step's settings."""
    checkout_indent = leading_spaces(lines[index])
    block: list[str] = []
    for candidate in lines[index + 1 :]:
        stripped = candidate.strip()
        indent = leading_spaces(candidate)
        if stripped.startswith("-") and indent <= checkout_indent:
            break
        block.append(candidate)
    return block


def external_action_ref(uses_value: str) -> tuple[str, str] | None:
    """Return (action, ref) for repository actions; ignore local and docker actions."""
    if uses_value.startswith("./") or uses_value.startswith("docker://"):
        return None
    if "@" not in uses_value:
        return (uses_value, "")
    action, ref = uses_value.rsplit("@", 1)
    return action, ref


def validate_workflow(path: Path) -> list[str]:
    """Return all GoreeVault workflow-security violations found in one workflow."""
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    if not any(TOP_LEVEL_PERMISSIONS_RE.match(line) for line in lines):
        errors.append("missing explicit top-level permissions boundary")

    checkout_count = 0
    for index, line in enumerate(lines):
        match = USES_RE.match(line)
        if not match:
            continue

        uses_value = match.group(1)
        external = external_action_ref(uses_value)
        if external is not None:
            action, ref = external
            if FULL_SHA_RE.fullmatch(ref) is None:
                errors.append(
                    f"line {index + 1}: external action {action} must be pinned to a full 40-character commit SHA"
                )

        checkout_match = CHECKOUT_RE.fullmatch(uses_value)
        if uses_value.startswith("actions/checkout@"):
            checkout_count += 1
            if checkout_match is None:
                # The generic external-action check already reports the weak ref.
                continue

            block = checkout_block(lines, index)
            if not any(
                candidate.strip() == "persist-credentials: false" for candidate in block
            ):
                errors.append(
                    f"line {index + 1}: checkout must set persist-credentials: false"
                )

    if checkout_count == 0:
        errors.append("workflow has no actions/checkout step to validate")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(".github/workflows"),
        help="Workflow directory to inspect (default: .github/workflows)",
    )
    args = parser.parse_args()

    workflows = sorted(args.root.glob("goreevault-*.yml"))
    if not workflows:
        print("No GoreeVault-owned workflows were found.", file=sys.stderr)
        return 1

    failures: list[str] = []
    for workflow in workflows:
        for error in validate_workflow(workflow):
            failures.append(f"{workflow}: {error}")

    if failures:
        print("GoreeVault workflow security validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Validated {len(workflows)} GoreeVault-owned workflows.")
    print("External actions are SHA-pinned, checkout credentials are not persisted, and permissions are explicit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
