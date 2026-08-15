#!/usr/bin/env python3
"""Unit tests for GoreeVault GitHub Actions security validation."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate-workflow-security.py"
SPEC = importlib.util.spec_from_file_location("goreevault_workflow_security", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator from {MODULE_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SHA_A = "a" * 40
SHA_B = "b" * 40


class WorkflowSecurityTests(unittest.TestCase):
    def write_workflow(self, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "goreevault-test.yml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_checkout_block_stops_at_next_step(self) -> None:
        lines = [
            "      - name: Checkout",
            f"        uses: actions/checkout@{SHA_A}",
            "      - run: echo next-step",
            "        with:",
            "          persist-credentials: false",
        ]
        block = VALIDATOR.checkout_block(lines, 1)
        self.assertNotIn("          persist-credentials: false", block)

    def test_checkout_block_keeps_own_with_block(self) -> None:
        lines = [
            "      - name: Checkout",
            f"        uses: actions/checkout@{SHA_A}",
            "        with:",
            "          persist-credentials: false",
            "      - run: echo done",
        ]
        block = VALIDATOR.checkout_block(lines, 1)
        self.assertIn("          persist-credentials: false", block)

    def test_permissions_boundary_accepts_supported_top_level_forms(self) -> None:
        for value in ("permissions:", "permissions: {}", "permissions: read-all", "permissions: write-all"):
            with self.subTest(value=value):
                self.assertIsNotNone(VALIDATOR.TOP_LEVEL_PERMISSIONS_RE.fullmatch(value))

    def test_permissions_boundary_rejects_indented_job_level_forms(self) -> None:
        for value in ("  permissions:", "  permissions: {}", "    permissions: read-all"):
            with self.subTest(value=value):
                self.assertIsNone(VALIDATOR.TOP_LEVEL_PERMISSIONS_RE.fullmatch(value))

    def test_external_action_ref_classification(self) -> None:
        self.assertEqual(VALIDATOR.external_action_ref(f"vendor/action@{SHA_B}"), ("vendor/action", SHA_B))
        self.assertEqual(VALIDATOR.external_action_ref("vendor/action@v4"), ("vendor/action", "v4"))
        self.assertIsNone(VALIDATOR.external_action_ref("./.github/actions/local"))
        self.assertIsNone(VALIDATOR.external_action_ref("docker://alpine:3.20"))

    def test_valid_workflow_passes(self) -> None:
        path = self.write_workflow(
            "\n".join(
                [
                    "name: test",
                    "permissions: {}",
                    "jobs:",
                    "  test:",
                    "    steps:",
                    "      - name: Checkout",
                    f"        uses: actions/checkout@{SHA_A}",
                    "        with:",
                    "          persist-credentials: false",
                    "      - name: External action",
                    f"        uses: vendor/action@{SHA_B}",
                ]
            )
        )
        self.assertEqual(VALIDATOR.validate_workflow(path), [])

    def test_mutable_external_action_is_rejected(self) -> None:
        path = self.write_workflow(
            "\n".join(
                [
                    "name: test",
                    "permissions: {}",
                    "jobs:",
                    "  test:",
                    "    steps:",
                    "      - name: Checkout",
                    f"        uses: actions/checkout@{SHA_A}",
                    "        with:",
                    "          persist-credentials: false",
                    "      - name: Mutable",
                    "        uses: vendor/action@v4",
                ]
            )
        )
        errors = VALIDATOR.validate_workflow(path)
        self.assertTrue(any("vendor/action" in error and "40-character" in error for error in errors))

    def test_checkout_without_nonpersistent_credentials_is_rejected(self) -> None:
        path = self.write_workflow(
            "\n".join(
                [
                    "name: test",
                    "permissions: read-all",
                    "jobs:",
                    "  test:",
                    "    steps:",
                    "      - name: Checkout",
                    f"        uses: actions/checkout@{SHA_A}",
                    "      - run: echo done",
                ]
            )
        )
        errors = VALIDATOR.validate_workflow(path)
        self.assertTrue(any("persist-credentials: false" in error for error in errors))

    def test_missing_top_level_permissions_is_rejected(self) -> None:
        path = self.write_workflow(
            "\n".join(
                [
                    "name: test",
                    "jobs:",
                    "  test:",
                    "    permissions:",
                    "      contents: read",
                    "    steps:",
                    "      - name: Checkout",
                    f"        uses: actions/checkout@{SHA_A}",
                    "        with:",
                    "          persist-credentials: false",
                ]
            )
        )
        errors = VALIDATOR.validate_workflow(path)
        self.assertIn("missing explicit top-level permissions boundary", errors)


if __name__ == "__main__":
    unittest.main()
