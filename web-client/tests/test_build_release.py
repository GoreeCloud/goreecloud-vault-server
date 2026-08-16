#!/usr/bin/env python3
"""Regression tests for the GoreeVault Web deterministic static release builder."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("goreevault_web_build_release", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SECURITY_RUNTIME_FILES = {
    "assets/aes-cbc-hmac.js",
    "assets/auth-kdf.js",
    "assets/authenticated-api.js",
    "assets/enc-string.js",
    "assets/identity-protocol.js",
    "assets/master-key-crypto.js",
    "assets/sync-client.js",
    "assets/token-state.js",
}
SOURCE_DATE_EPOCH = 1786871196
EXPECTED_CREATED_AT = "2026-08-16T09:06:36Z"


def checksum_map(spdx_file: dict[str, object]) -> dict[str, str]:
    return {
        str(checksum["algorithm"]): str(checksum["checksumValue"])
        for checksum in spdx_file["checksums"]
    }


class ReleaseBuildTests(unittest.TestCase):
    def test_manifest_is_deterministic_for_same_source(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = MODULE.build(Path(first_dir), "abc123", SOURCE_DATE_EPOCH)
            second = MODULE.build(Path(second_dir), "abc123", SOURCE_DATE_EPOCH)
            self.assertEqual(first, second)
            self.assertEqual(first["runtimeDependencies"], [])
            self.assertEqual(first["product"], "GoreeVault Web")
            self.assertEqual(first["schema"], 2)
            self.assertEqual(first["sourceDateEpoch"], SOURCE_DATE_EPOCH)
            self.assertEqual(
                (Path(first_dir) / MODULE.SBOM_NAME).read_bytes(),
                (Path(second_dir) / MODULE.SBOM_NAME).read_bytes(),
            )

    def test_release_contains_only_explicit_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            manifest = MODULE.build(output, "abc123", SOURCE_DATE_EPOCH)
            paths = [entry["path"] for entry in manifest["files"]]
            self.assertEqual(paths, list(MODULE.RELEASE_FILES))
            self.assertNotIn("package.json", paths)
            self.assertNotIn("docs/SECURITY-BOUNDARY.md", paths)
            self.assertNotIn("tests/auth-protocol.test.js", paths)
            self.assertTrue((output / "release-manifest.json").is_file())
            self.assertTrue((output / MODULE.SBOM_NAME).is_file())

    def test_release_contains_security_runtime_and_glaze_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = MODULE.build(Path(temp_dir), "abc123", SOURCE_DATE_EPOCH)
            paths = {entry["path"] for entry in manifest["files"]}
            self.assertTrue(SECURITY_RUNTIME_FILES.issubset(paths))
            self.assertIn("assets/feedback.css", paths)
            self.assertIn("assets/glaze.css", paths)

    def test_manifest_records_sha256_size_and_sbom_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            manifest = MODULE.build(output, "abc123", SOURCE_DATE_EPOCH)
            for entry in manifest["files"]:
                self.assertEqual(len(entry["sha256"]), 64)
                int(entry["sha256"], 16)
                self.assertGreater(entry["bytes"], 0)
            sbom_path = output / MODULE.SBOM_NAME
            self.assertEqual(manifest["sbom"]["format"], "SPDX-2.3")
            self.assertEqual(manifest["sbom"]["path"], MODULE.SBOM_NAME)
            self.assertEqual(manifest["sbom"]["sha256"], MODULE.sha256(sbom_path))
            self.assertEqual(manifest["sbom"]["bytes"], sbom_path.stat().st_size)

    def test_spdx_sbom_binds_source_files_and_creation_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            manifest = MODULE.build(output, "abc123", SOURCE_DATE_EPOCH)
            sbom = json.loads((output / MODULE.SBOM_NAME).read_text(encoding="utf-8"))

            self.assertEqual(sbom["spdxVersion"], "SPDX-2.3")
            self.assertEqual(sbom["dataLicense"], "CC0-1.0")
            self.assertEqual(sbom["SPDXID"], "SPDXRef-DOCUMENT")
            self.assertEqual(sbom["creationInfo"]["created"], EXPECTED_CREATED_AT)
            self.assertEqual(
                sbom["documentNamespace"],
                "https://goreecloud.com/spdx/goreevault-web/abc123",
            )
            self.assertEqual(len(sbom["packages"]), 1)
            package = sbom["packages"][0]
            self.assertTrue(package["filesAnalyzed"])
            self.assertEqual(package["primaryPackagePurpose"], "APPLICATION")

            spdx_by_path = {entry["fileName"][2:]: entry for entry in sbom["files"]}
            self.assertEqual(set(spdx_by_path), set(MODULE.RELEASE_FILES))
            sha1_values = []
            for manifest_entry in manifest["files"]:
                relative = manifest_entry["path"]
                target = output / relative
                checksums = checksum_map(spdx_by_path[relative])
                expected_sha1 = hashlib.sha1(target.read_bytes()).hexdigest()
                sha1_values.append(expected_sha1)
                self.assertEqual(checksums["SHA1"], expected_sha1)
                self.assertEqual(checksums["SHA256"], manifest_entry["sha256"])

            self.assertEqual(
                package["packageVerificationCode"]["packageVerificationCodeValue"],
                MODULE.verification_code(sha1_values),
            )

    def test_spdx_relationships_describe_and_contain_all_release_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            MODULE.build(output, "abc123", SOURCE_DATE_EPOCH)
            sbom = json.loads((output / MODULE.SBOM_NAME).read_text(encoding="utf-8"))
            relationships = sbom["relationships"]
            self.assertIn(
                {
                    "spdxElementId": "SPDXRef-DOCUMENT",
                    "relationshipType": "DESCRIBES",
                    "relatedSpdxElement": "SPDXRef-Package-GoreeVault-Web",
                },
                relationships,
            )
            contained = {
                relation["relatedSpdxElement"]
                for relation in relationships
                if relation["spdxElementId"] == "SPDXRef-Package-GoreeVault-Web"
                and relation["relationshipType"] == "CONTAINS"
            }
            self.assertEqual(
                contained,
                {MODULE.spdx_file_id(relative) for relative in MODULE.RELEASE_FILES},
            )

    def test_negative_source_date_epoch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "source date epoch"):
                MODULE.build(Path(temp_dir), "abc123", -1)


if __name__ == "__main__":
    unittest.main()
