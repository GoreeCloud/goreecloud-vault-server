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

CHECKOUT_RE = re.compile(r"^\s*uses:\s*actions/checkout@([0-9a-f]{40})\s*(?:#.*)?$")
CHECKOUT_ANY_RE = re.compile(r"^\s*uses:\s*actions/checkout@([^\s#]+)")


class ValidationError(ValueError):
    pass


def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def validate_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    if not any(line.startswith("permissions:") for line in lines):
        errors.append("missing explicit top-level permissions boundary")

    checkout_count = 0
    for index, line in enumerate(lines):
        match_any = CHECKOUT_ANY_RE.match(line)
        if not match_any:
            continue

        checkout_count += 1
        if CHECKOUT_RE.match(line) is None:
            errors.append(
                f"line {index + 1}: actions/checkout must be pinned to a full 40-character commit SHA"
            )

        checkout_indent = leading_spaces(line)
        block: list[str] = []
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            indent = leading_spaces(candidate)
            if stripped.startswith("- name:") and indent <= checkout_indent:
                break
            if stripped.startswith("- uses:") and indent <= checkout_indent:
                break
            block.append(candidate)

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
    print("Checkout actions are SHA-pinned, credentials are not persisted, and permissions are explicit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
