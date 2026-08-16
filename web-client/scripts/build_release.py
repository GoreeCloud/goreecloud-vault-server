#!/usr/bin/env python3
"""Build a deterministic static GoreeVault Web release directory and SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dist"
RELEASE_FILES = (
    "index.html",
    "assets/api-client.js",
    "assets/api-errors.js",
    "assets/app.js",
    "assets/auth-protocol.js",
    "assets/auth-request.js",
    "assets/auth-state.js",
    "assets/crypto-boundary.js",
    "assets/glaze.css",
    "assets/goreevault-mark.svg",
    "assets/runtime-config.js",
    "assets/server-config.js",
    "assets/session-state.js",
    "assets/sync-protocol.js",
    "assets/theme-init.js",
    "assets/vault-state.js",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(out: Path, source_revision: str) -> dict[str, object]:
    if out.resolve() == ROOT.resolve():
        raise ValueError("release output must not overwrite the source tree")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    files: list[dict[str, object]] = []
    for relative in RELEASE_FILES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(f"required release file missing: {relative}")
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files.append({
            "path": relative,
            "sha256": sha256(target),
            "bytes": target.stat().st_size,
        })

    manifest: dict[str, object] = {
        "schema": 1,
        "product": "GoreeVault Web",
        "channel": "pre-alpha",
        "sourceRevision": source_revision,
        "runtimeDependencies": [],
        "files": files,
    }
    manifest_path = out / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--source-revision", default="unverified-local")
    args = parser.parse_args()
    manifest = build(args.out, args.source_revision)
    print(f"Built {len(manifest['files'])} GoreeVault Web release files at {args.out}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
