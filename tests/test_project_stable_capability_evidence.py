#!/usr/bin/env python3
"""Tests for bounded GoreeCloud Vault Server capability evidence projection."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECTOR_PATH = ROOT / "scripts" / "project-stable-capability-evidence.py"
EXAMPLE_PATH = ROOT / "docs" / "stable-evidence.example.json"

SPEC = importlib.util.spec_from_file_location("goreevault_capability_evidence", PROJECTOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load capability projector from {PROJECTOR_PATH}")
PROJECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROJECTOR)

SOURCE_SHA = "1" * 40
MANIFEST_DIGEST = "sha256:" + "2" * 64
RC_TAG = "v0.3.0-rc.1"


def replace_placeholders(value: Any) -> Any:
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
    data = PROJECTOR.VALIDATOR.load_json_strict(EXAMPLE_PATH.read_text(encoding="utf-8"))
    cleaned = replace_placeholders(data)
    assert isinstance(cleaned, dict)
    return cleaned


class StableCapabilityEvidenceProjectionTests(unittest.TestCase):
    def project(self, data: dict[str, Any]) -> dict[str, Any]:
        return PROJECTOR.project_capability_evidence(
            data,
            expected_source_sha=SOURCE_SHA,
            expected_rc_tag=RC_TAG,
            expected_manifest_digest=MANIFEST_DIGEST,
        )

    def test_exact_validated_candidate_projects_minimized_capability(self) -> None:
        projection = self.project(complete_evidence())
        self.assertEqual(projection["service"], "vault")
        self.assertEqual(projection["validation_scope"], "stable-evidence-exact-pinned")
        self.assertFalse(projection["contains_user_content"])
        self.assertFalse(projection["credentials_exposed"])
        self.assertFalse(projection["runtime_deployment_evaluated"])

        capabilities = projection["capabilities"]
        self.assertEqual(len(capabilities), 1)
        capability = capabilities[0]
        self.assertEqual(capability["id"], "vault.secrets")
        self.assertTrue(capability["authoritative"])
        self.assertTrue(capability["current"])
        self.assertTrue(capability["stable_evidence_accepted"])
        self.assertFalse(capability["production_accepted"])

    def test_projection_does_not_leak_reviewers_or_raw_evidence_references(self) -> None:
        projection = self.project(complete_evidence())
        serialized = str(projection).lower()
        self.assertNotIn("reviewer", serialized)
        self.assertNotIn("evidence_reference", serialized)
        self.assertNotIn("backup_reference", serialized)
        self.assertNotIn("rollback_reference", serialized)

    def test_projection_requires_exact_candidate_identity(self) -> None:
        data = complete_evidence()
        with self.assertRaises(PROJECTOR.VALIDATOR.EvidenceError):
            PROJECTOR.project_capability_evidence(
                data,
                expected_source_sha="f" * 40,
                expected_rc_tag=RC_TAG,
                expected_manifest_digest=MANIFEST_DIGEST,
            )


if __name__ == "__main__":
    unittest.main()
