#!/usr/bin/env python3
"""Regression tests for the GoreeVault Web deterministic static release builder."""

from __future__ import annotations

import importlib.util
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


class ReleaseBuildTests(unittest.TestCase):
    def test_manifest_is_deterministic_for_same_source(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = MODULE.build(Path(first_dir), "abc123")
            second = MODULE.build(Path(second_dir), "abc123")
            self.assertEqual(first, second)
            self.assertEqual(first["runtimeDependencies"], [])
            self.assertEqual(first["product"], "GoreeVault Web")

    def test_release_contains_only_explicit_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            manifest = MODULE.build(output, "abc123")
            paths = [entry["path"] for entry in manifest["files"]]
            self.assertEqual(paths, list(MODULE.RELEASE_FILES))
            self.assertNotIn("package.json", paths)
            self.assertNotIn("docs/SECURITY-BOUNDARY.md", paths)
            self.assertNotIn("tests/auth-protocol.test.js", paths)
            self.assertTrue((output / "release-manifest.json").is_file())

    def test_release_contains_security_runtime_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = MODULE.build(Path(temp_dir), "abc123")
            paths = {entry["path"] for entry in manifest["files"]}
            self.assertTrue(SECURITY_RUNTIME_FILES.issubset(paths))

    def test_manifest_records_sha256_and_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = MODULE.build(Path(temp_dir), "abc123")
            for entry in manifest["files"]:
                self.assertEqual(len(entry["sha256"]), 64)
                int(entry["sha256"], 16)
                self.assertGreater(entry["bytes"], 0)


if __name__ == "__main__":
    unittest.main()
