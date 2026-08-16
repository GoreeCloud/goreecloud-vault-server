#!/usr/bin/env python3
"""Create fail-closed identity evidence for the build-only GoreeVault Argon2id WASM core."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

WASM_MAGIC = b"\x00asm"
WASM_VERSION_1 = b"\x01\x00\x00\x00"
SCHEMA_VERSION = 1


def build_evidence(wasm_path: Path, source_revision: str) -> dict[str, object]:
    """Return deterministic evidence for one exact build-only WASM artifact."""
    if len(source_revision) != 40 or any(ch not in "0123456789abcdef" for ch in source_revision):
        raise ValueError("source revision must be a lowercase 40-character Git SHA")

    payload = wasm_path.read_bytes()
    if len(payload) <= 8:
        raise ValueError("WASM artifact is empty or contains only a header")
    if payload[:4] != WASM_MAGIC or payload[4:8] != WASM_VERSION_1:
        raise ValueError("artifact is not a WebAssembly 1.0 module")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "artifact": {
            "path": wasm_path.name,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
        "sourceRevision": source_revision,
        "runtimeIntegrationApproved": False,
        "credentialProcessingApproved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wasm", required=True, type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    evidence = build_evidence(args.wasm, args.source_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
