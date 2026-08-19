#!/usr/bin/env python3
"""Build deterministic, validation-only evidence for browser Argon2id bindings.

This tool packages generated ``wasm-bindgen --target web`` files into an isolated
candidate-evidence directory. It does not modify the GoreeVault Web production
release allowlist and it never grants runtime-integration or credential-processing
approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import quote

PREFIX = "goreevault_web_argon2id_core"
REQUIRED_FILES = {
    f"{PREFIX}.js",
    f"{PREFIX}_bg.wasm",
}
ALLOWED_SUFFIXES = (".js", ".wasm", ".d.ts")
SPDX_VERSION = "SPDX-2.3"


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def discover_bindings(bindings: Path) -> list[Path]:
    if not bindings.is_dir():
        raise ValueError("bindings path must be a directory")

    files: list[Path] = []
    for candidate in sorted(bindings.iterdir(), key=lambda item: item.name):
        if candidate.is_symlink():
            raise ValueError(f"binding evidence refuses symlink: {candidate.name}")
        if not candidate.is_file():
            continue
        if not candidate.name.startswith(PREFIX):
            raise ValueError(f"unexpected browser binding file: {candidate.name}")
        if not candidate.name.endswith(ALLOWED_SUFFIXES):
            raise ValueError(f"unsupported browser binding file type: {candidate.name}")
        files.append(candidate)

    names = {path.name for path in files}
    missing = sorted(REQUIRED_FILES - names)
    if missing:
        raise ValueError(f"required browser binding files missing: {', '.join(missing)}")
    return files


def spdx_id(filename: str) -> str:
    return f"SPDXRef-File-{hashlib.sha256(filename.encode('utf-8')).hexdigest()[:20]}"


def build(bindings: Path, output: Path, source_revision: str, wasm_bindgen_version: str) -> dict[str, object]:
    if not source_revision or source_revision == "unverified-local":
        raise ValueError("an exact source revision is required")
    if not wasm_bindgen_version:
        raise ValueError("wasm-bindgen version is required")
    if output.resolve() == bindings.resolve():
        raise ValueError("output must be separate from generated bindings")

    source_files = discover_bindings(bindings)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    files: list[dict[str, object]] = []
    spdx_files: list[dict[str, object]] = []
    relationships: list[dict[str, str]] = [
        {
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": "SPDXRef-Package-GoreeVault-Web-Argon2id-Candidate",
        }
    ]

    for source in source_files:
        target = output / source.name
        shutil.copyfile(source, target)
        sha256 = digest(target, "sha256")
        sha1 = digest(target, "sha1")
        files.append({"path": source.name, "sha256": sha256, "bytes": target.stat().st_size})
        file_id = spdx_id(source.name)
        spdx_files.append(
            {
                "fileName": f"./{source.name}",
                "SPDXID": file_id,
                "checksums": [
                    {"algorithm": "SHA1", "checksumValue": sha1},
                    {"algorithm": "SHA256", "checksumValue": sha256},
                ],
                "licenseConcluded": "NOASSERTION",
                "licenseInfoInFiles": ["NOASSERTION"],
                "copyrightText": "NOASSERTION",
            }
        )
        relationships.append(
            {
                "spdxElementId": "SPDXRef-Package-GoreeVault-Web-Argon2id-Candidate",
                "relationshipType": "CONTAINS",
                "relatedSpdxElement": file_id,
            }
        )

    sbom = {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"GoreeVault-Web-Argon2id-Candidate-{source_revision}",
        "documentNamespace": (
            "https://goreecloud.com/spdx/goreevault-web/argon2id-candidate/"
            f"{quote(source_revision, safe='')}"
        ),
        "creationInfo": {
            "created": "1970-01-01T00:00:00Z",
            "creators": ["Tool: GoreeVault browser Argon2id candidate evidence builder"],
        },
        "packages": [
            {
                "name": "GoreeVault Web Argon2id Browser Candidate",
                "SPDXID": "SPDXRef-Package-GoreeVault-Web-Argon2id-Candidate",
                "versionInfo": source_revision,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": True,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "primaryPackagePurpose": "LIBRARY",
            }
        ],
        "files": spdx_files,
        "relationships": relationships,
    }
    sbom_path = output / "sbom.spdx.json"
    sbom_path.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest: dict[str, object] = {
        "schema": 1,
        "artifactType": "validation-only-browser-crypto-candidate",
        "product": "GoreeVault Web Argon2id",
        "sourceRevision": source_revision,
        "wasmBindgenVersion": wasm_bindgen_version,
        "runtimeIntegrationApproved": False,
        "credentialProcessingApproved": False,
        "productionReleaseInclusionApproved": False,
        "files": files,
        "sbom": {
            "format": SPDX_VERSION,
            "path": sbom_path.name,
            "sha256": digest(sbom_path, "sha256"),
            "bytes": sbom_path.stat().st_size,
        },
    }
    manifest_path = output / "candidate-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--wasm-bindgen-version", required=True)
    args = parser.parse_args()
    manifest = build(args.bindings, args.output, args.source_revision, args.wasm_bindgen_version)
    print(
        f"Built validation-only browser candidate evidence for {len(manifest['files'])} generated files at {args.output}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
