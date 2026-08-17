#!/usr/bin/env python3
"""Create deterministic fail-closed evidence for generated GoreeVault Argon2id bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA_VERSION = 1


def _require_revision(value: str) -> str:
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("source revision must be a lowercase 40-character Git SHA")
    return value


def _require_version(value: str) -> str:
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("wasm-bindgen version must use numeric x.y.z form")
    return value


def build_evidence(binding_dir: Path, source_revision: str, wasm_bindgen_version: str) -> dict[str, object]:
    """Return deterministic identities for every generated binding artifact."""
    _require_revision(source_revision)
    _require_version(wasm_bindgen_version)
    if not binding_dir.is_dir():
        raise ValueError("binding directory does not exist")

    files: list[dict[str, object]] = []
    for path in sorted((item for item in binding_dir.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        payload = path.read_bytes()
        if not payload:
            raise ValueError(f"generated binding artifact is empty: {path.name}")
        files.append(
            {
                "path": path.relative_to(binding_dir).as_posix(),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    if not files:
        raise ValueError("binding directory contains no generated files")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "sourceRevision": source_revision,
        "generator": {"name": "wasm-bindgen-cli", "version": wasm_bindgen_version},
        "files": files,
        "runtimeIntegrationApproved": False,
        "credentialProcessingApproved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindings", required=True, type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--wasm-bindgen-version", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    evidence = build_evidence(args.bindings, args.source_revision, args.wasm_bindgen_version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
