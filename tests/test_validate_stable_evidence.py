#!/usr/bin/env python3
"""Unit tests for the fail-closed GoreeVault Stable-evidence validator."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate-stable-evidence.py"
EXAMPLE_PATH = ROOT / "docs" / "stable-evidence.example.json"

SPEC = importlib.util.spec_from_file_location("goreevault_stable_evidence", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator from {MODULE_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SOURCE_SHA = "1" * 40
MANIFEST_DIGEST = "sha256:" + "2" * 64
RC_TAG = "v0.3.0-rc.1"


def replace_placeholders(value: Any) -> Any:
    """Turn the documented template into deterministic, non-placeholder evidence."""
    if isinstance(value, dict):
        return {key: replace_placeholders(child) for key, child in value.items()}
    if isinstance(value, list):
        return [replace_placeholders(child) for child in value]
    if isinstance(value, str) and "REPLACE_ME" in value:
        if "@sha256:" in value:
            digest = value.split("@", 1)[1]
            return f"goreevault-test-artifact@{digest}"
        return "recorded-test-evidence"
    return value


def complete_evidence() -> dict[str, Any]:
    raw = EXAMPLE_PATH.read_text(encoding="utf-8")
    data = VALIDATOR.load_json_strict(raw)
    cleaned = replace_placeholders(data)
    assert isinstance(cleaned, dict)
    return cleaned


class StableEvidenceValidatorTests(unittest.TestCase):
    def validate(self, data: dict[str, Any], **overrides: Any) -> None:
        arguments = {
            "expected_source_sha": SOURCE_SHA,
            "expected_rc_tag": RC_TAG,
            "expected_manifest_digest": MANIFEST_DIGEST,
            "allow_placeholders": False,
        }
        arguments.update(overrides)
        VALIDATOR.validate_evidence(data, **arguments)

    def test_complete_schema_v2_example_passes_after_placeholders_are_resolved(self) -> None:
        self.validate(complete_evidence())

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(VALIDATOR.EvidenceError, "duplicate JSON key"):
            VALIDATOR.load_json_strict('{"schema_version": 2, "schema_version": 2}')

    def test_unresolved_template_placeholder_is_rejected(self) -> None:
        raw = EXAMPLE_PATH.read_text(encoding="utf-8")
        data = VALIDATOR.load_json_strict(raw)
        with self.assertRaisesRegex(VALIDATOR.EvidenceError, "template placeholder"):
            self.validate(data)

    def test_exact_source_sha_binding_is_enforced(self) -> None:
        data = complete_evidence()
        with self.assertRaises(VALIDATOR.EvidenceError):
            self.validate(data, expected_source_sha="f" * 40)

    def test_exact_rc_tag_binding_is_enforced(self) -> None:
        data = complete_evidence()
        with self.assertRaises(VALIDATOR.EvidenceError):
            self.validate(data, expected_rc_tag="v9.9.9-rc.9")

    def test_exact_manifest_digest_binding_is_enforced(self) -> None:
        data = complete_evidence()
        with self.assertRaises(VALIDATOR.EvidenceError):
            self.validate(data, expected_manifest_digest="sha256:" + "f" * 64)

    def test_timestamp_without_timezone_is_rejected(self) -> None:
        with self.assertRaisesRegex(VALIDATOR.EvidenceError, "timezone offset"):
            VALIDATOR.parse_timestamp("2026-08-15T12:00:00", "tested_at")

    def test_unknown_root_field_is_rejected(self) -> None:
        data = copy.deepcopy(complete_evidence())
        data["unexpected"] = True
        with self.assertRaisesRegex(VALIDATOR.EvidenceError, "unknown fields"):
            self.validate(data)

    def test_false_required_glaze_control_is_rejected(self) -> None:
        data = copy.deepcopy(complete_evidence())
        data["glaze_ui"]["product_wide_conformance"] = False
        with self.assertRaisesRegex(VALIDATOR.EvidenceError, "product_wide_conformance"):
            self.validate(data)

    def test_governance_control_cannot_be_silently_removed(self) -> None:
        data = copy.deepcopy(complete_evidence())
        del data["governance"]["main_protected"]
        with self.assertRaisesRegex(VALIDATOR.EvidenceError, "missing required fields"):
            self.validate(data)


if __name__ == "__main__":
    unittest.main()
