#!/usr/bin/env python3
"""Regression tests for deterministic GoreeVault Argon2id binding evidence."""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("build_binding_evidence.py")
spec = importlib.util.spec_from_file_location("build_binding_evidence", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

REVISION = "0123456789abcdef0123456789abcdef01234567"


def require_failure(callback, expected: str) -> None:
    try:
        callback()
    except ValueError as error:
        assert expected in str(error)
    else:
        raise AssertionError(f"expected ValueError containing {expected!r}")


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bindings = root / "bindings"
        bindings.mkdir()
        (bindings / "z.wasm").write_bytes(b"\x00asm\x01\x00\x00\x00payload")
        (bindings / "a.js").write_text("module.exports = {};\n", encoding="utf-8")

        evidence = module.build_evidence(bindings, REVISION, "0.2.126")
        assert evidence["sourceRevision"] == REVISION
        assert evidence["generator"] == {"name": "wasm-bindgen-cli", "version": "0.2.126"}
        assert [entry["path"] for entry in evidence["files"]] == ["a.js", "z.wasm"]
        assert evidence["runtimeIntegrationApproved"] is False
        assert evidence["credentialProcessingApproved"] is False
        first = module.build_evidence(bindings, REVISION, "0.2.126")
        assert evidence == first

        empty = root / "empty"
        empty.mkdir()
        require_failure(lambda: module.build_evidence(empty, REVISION, "0.2.126"), "no generated files")
        require_failure(lambda: module.build_evidence(bindings, "BAD", "0.2.126"), "source revision")
        require_failure(lambda: module.build_evidence(bindings, REVISION, "latest"), "numeric x.y.z")
        (bindings / "empty.js").write_bytes(b"")
        require_failure(lambda: module.build_evidence(bindings, REVISION, "0.2.126"), "is empty")

    print("GoreeVault Argon2id binding evidence tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
