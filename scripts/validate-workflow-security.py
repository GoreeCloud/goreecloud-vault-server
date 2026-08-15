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


def validate_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    if not any(TOP_LEVEL_PERMISSIONS_RE.match(line) for line in lines):
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


def run_self_tests() -> list[str]:
    """Exercise parser and permissions boundaries that could create false passes."""
    failures: list[str] = []

    boundary_lines = [
        "      - name: Checkout one",
        "        uses: actions/checkout@" + "a" * 40,
        "      - run: echo next-step",
        "        with:",
        "          persist-credentials: false",
    ]
    if any(
        line.strip() == "persist-credentials: false"
        for line in checkout_block(boundary_lines, 1)
    ):
        failures.append("checkout step parser leaked into a later run step")

    valid_lines = [
        "      - name: Checkout",
        "        uses: actions/checkout@" + "a" * 40,
        "        with:",
        "          persist-credentials: false",
        "      - run: echo done",
    ]
    if not any(
        line.strip() == "persist-credentials: false"
        for line in checkout_block(valid_lines, 1)
    ):
        failures.append("checkout step parser rejected an in-step credential setting")

    if TOP_LEVEL_PERMISSIONS_RE.match("  permissions:"):
        failures.append("job-level permissions were accepted as top-level permissions")
    if TOP_LEVEL_PERMISSIONS_RE.match("  permissions: {}"):
        failures.append("indented empty permissions were accepted as top-level permissions")
    if TOP_LEVEL_PERMISSIONS_RE.match("permissions: {}") is None:
        failures.append("explicit empty top-level permissions were rejected")
    if TOP_LEVEL_PERMISSIONS_RE.match("permissions:") is None:
        failures.append("block-style top-level permissions were rejected")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(".github/workflows"),
        help="Workflow directory to inspect (default: .github/workflows)",
    )
    args = parser.parse_args()

    self_test_failures = run_self_tests()
    if self_test_failures:
        print("GoreeVault workflow security validator self-test failed:", file=sys.stderr)
        for failure in self_test_failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

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
