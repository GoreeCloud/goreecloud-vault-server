#!/usr/bin/env python3
"""Regression tests for build-only GoreeVault Argon2id WASM identity evidence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from build_wasm_evidence import build_evidence


class BuildWasmEvidenceTests(unittest.TestCase):
    def test_valid_module_is_bound_to_source_and_fail_closed_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wasm = Path(tmp) / "argon2id.wasm"
            wasm.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"\x00\x01\x00")
            evidence = build_evidence(wasm, "a" * 40)

        self.assertEqual(evidence["schemaVersion"], 1)
        self.assertEqual(evidence["sourceRevision"], "a" * 40)
        self.assertFalse(evidence["runtimeIntegrationApproved"])
        self.assertFalse(evidence["credentialProcessingApproved"])
        self.assertEqual(evidence["artifact"]["path"], "argon2id.wasm")
        self.assertEqual(evidence["artifact"]["bytes"], 11)
        self.assertEqual(len(evidence["artifact"]["sha256"]), 64)

    def test_rejects_non_wasm_and_header_only_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.wasm"
            path.write_bytes(b"not-wasm")
            with self.assertRaises(ValueError):
                build_evidence(path, "b" * 40)

            path.write_bytes(b"\x00asm\x01\x00\x00\x00")
            with self.assertRaises(ValueError):
                build_evidence(path, "b" * 40)

    def test_rejects_non_exact_source_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wasm = Path(tmp) / "argon2id.wasm"
            wasm.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"\x00\x01\x00")
            for revision in ("c" * 39, "C" * 40, "g" * 40):
                with self.subTest(revision=revision):
                    with self.assertRaises(ValueError):
                        build_evidence(wasm, revision)


if __name__ == "__main__":
    unittest.main()
