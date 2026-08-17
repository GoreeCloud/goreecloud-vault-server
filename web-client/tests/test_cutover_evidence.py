from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_cutover_evidence.py"
SPEC = importlib.util.spec_from_file_location("validate_cutover_evidence", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def final_record() -> dict[str, object]:
    return {
        "schema": 1,
        "product": "GoreeVault Web",
        "status": "final",
        "previousClient": {
            "name": "Bundled upstream-compatible web vault",
            "version": "2026.7.0",
            "artifactIdentity": "web-vault-2026.7.0",
        },
        "candidate": {
            "sourceRevision": "a" * 40,
            "artifactSha256": "b" * 64,
            "releaseManifestSha256": "c" * 64,
            "sbomSha256": "d" * 64,
        },
        "server": {
            "sourceRevision": "e" * 40,
            "ociManifestDigest": f"sha256:{'f' * 64}",
        },
        "evidence": {
            "compatibility": "release-assets/compatibility.json",
            "accessibility": "release-assets/accessibility.json",
            "security": "release-assets/security.json",
            "rollback": "release-assets/rollback.json",
        },
        "rollback": {
            "procedure": "docs/browser-rollback.md",
            "requiresDatabaseDowngrade": False,
            "requiresPlaintextExport": False,
        },
        "operator": {
            "name": "GoreeCloud release operator",
            "timestamp": "2026-08-16T19:15:00Z",
        },
        "outcome": "accepted",
    }


def template_record() -> dict[str, object]:
    record = final_record()
    record["status"] = "template"
    record["previousClient"]["version"] = "TBD"
    record["candidate"]["sourceRevision"] = "TBD"
    record["candidate"]["artifactSha256"] = "TBD"
    record["candidate"]["releaseManifestSha256"] = "TBD"
    record["candidate"]["sbomSha256"] = "TBD"
    record["server"]["sourceRevision"] = "TBD"
    record["server"]["ociManifestDigest"] = "TBD"
    for key in record["evidence"]:
        record["evidence"][key] = "TBD"
    record["rollback"]["procedure"] = "TBD"
    record["operator"]["name"] = "TBD"
    record["operator"]["timestamp"] = "TBD"
    record["outcome"] = "pending"
    return record


class CutoverEvidenceTests(unittest.TestCase):
    def test_complete_final_record_passes(self) -> None:
        validated = MODULE.validate_record(final_record())
        self.assertEqual(validated["status"], "final")
        self.assertEqual(validated["outcome"], "accepted")

    def test_template_requires_explicit_template_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "template evidence cannot satisfy"):
            MODULE.validate_record(template_record())
        validated = MODULE.validate_record(template_record(), allow_template=True)
        self.assertEqual(validated["status"], "template")

    def test_final_record_rejects_placeholders(self) -> None:
        record = final_record()
        record["evidence"]["accessibility"] = "TBD"
        with self.assertRaisesRegex(ValueError, "placeholder"):
            MODULE.validate_record(record)

    def test_rollback_cannot_require_database_downgrade(self) -> None:
        record = final_record()
        record["rollback"]["requiresDatabaseDowngrade"] = True
        with self.assertRaisesRegex(ValueError, "database downgrade"):
            MODULE.validate_record(record)

    def test_rollback_cannot_require_plaintext_export(self) -> None:
        record = final_record()
        record["rollback"]["requiresPlaintextExport"] = True
        with self.assertRaisesRegex(ValueError, "plaintext export"):
            MODULE.validate_record(record)

    def test_invalid_immutable_identity_is_rejected(self) -> None:
        record = final_record()
        record["server"]["ociManifestDigest"] = "sha256:not-a-digest"
        with self.assertRaisesRegex(ValueError, "invalid immutable identity"):
            MODULE.validate_record(record)

    def test_operator_timestamp_requires_timezone(self) -> None:
        record = final_record()
        record["operator"]["timestamp"] = "2026-08-16T19:15:00"
        with self.assertRaisesRegex(ValueError, "include a timezone"):
            MODULE.validate_record(record)

    def test_unexpected_fields_are_rejected_to_keep_evidence_minimal(self) -> None:
        record = final_record()
        record["accessToken"] = "must-never-be-recorded"
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            MODULE.validate_record(record)

    def test_final_outcome_must_be_terminal(self) -> None:
        record = final_record()
        record["outcome"] = "pending"
        with self.assertRaisesRegex(ValueError, "final outcome"):
            MODULE.validate_record(record)


if __name__ == "__main__":
    unittest.main()
