#!/usr/bin/env python3
"""Regression tests for build_browser_candidate_evidence.py."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_browser_candidate_evidence import build


def write_binding_set(root: Path) -> None:
    (root / "goreevault_web_argon2id_core.js").write_text("export default function init() {}\n", encoding="utf-8")
    (root / "goreevault_web_argon2id_core_bg.wasm").write_bytes(b"\x00asm-test")
    (root / "goreevault_web_argon2id_core.d.ts").write_text("export default function init(): void;\n", encoding="utf-8")


def test_build_is_deterministic_and_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bindings = root / "bindings"
        bindings.mkdir()
        write_binding_set(bindings)
        first = root / "first"
        second = root / "second"

        manifest_a = build(bindings, first, "abc123", "0.2.126")
        manifest_b = build(bindings, second, "abc123", "0.2.126")

        assert manifest_a == manifest_b
        assert manifest_a["runtimeIntegrationApproved"] is False
        assert manifest_a["credentialProcessingApproved"] is False
        assert manifest_a["productionReleaseInclusionApproved"] is False
        assert (first / "candidate-manifest.json").read_bytes() == (second / "candidate-manifest.json").read_bytes()
        assert (first / "sbom.spdx.json").read_bytes() == (second / "sbom.spdx.json").read_bytes()

        parsed = json.loads((first / "candidate-manifest.json").read_text(encoding="utf-8"))
        assert parsed["sourceRevision"] == "abc123"
        assert parsed["wasmBindgenVersion"] == "0.2.126"
        assert {entry["path"] for entry in parsed["files"]} >= {
            "goreevault_web_argon2id_core.js",
            "goreevault_web_argon2id_core_bg.wasm",
        }


def test_rejects_unverified_revision() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bindings = root / "bindings"
        bindings.mkdir()
        write_binding_set(bindings)
        try:
            build(bindings, root / "out", "unverified-local", "0.2.126")
        except ValueError as exc:
            assert "exact source revision" in str(exc)
        else:
            raise AssertionError("unverified source revision was accepted")


def test_rejects_unexpected_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bindings = root / "bindings"
        bindings.mkdir()
        write_binding_set(bindings)
        (bindings / "unexpected.txt").write_text("nope", encoding="utf-8")
        try:
            build(bindings, root / "out", "abc123", "0.2.126")
        except ValueError as exc:
            assert "unexpected browser binding file" in str(exc)
        else:
            raise AssertionError("unexpected binding file was accepted")


def test_rejects_symlinks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bindings = root / "bindings"
        bindings.mkdir()
        write_binding_set(bindings)
        target = root / "outside.js"
        target.write_text("outside", encoding="utf-8")
        (bindings / "goreevault_web_argon2id_core_extra.js").symlink_to(target)
        try:
            build(bindings, root / "out", "abc123", "0.2.126")
        except ValueError as exc:
            assert "refuses symlink" in str(exc)
        else:
            raise AssertionError("symlinked binding file was accepted")


def main() -> int:
    test_build_is_deterministic_and_fail_closed()
    test_rejects_unverified_revision()
    test_rejects_unexpected_files()
    test_rejects_symlinks()
    print("browser candidate evidence tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
