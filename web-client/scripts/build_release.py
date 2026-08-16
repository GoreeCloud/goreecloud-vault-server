#!/usr/bin/env python3
"""Build a deterministic static GoreeVault Web release directory, manifest, and SPDX SBOM."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dist"
SPDX_VERSION = "SPDX-2.3"
SBOM_NAME = "sbom.spdx.json"
RELEASE_FILES = (
    "index.html",
    "assets/account-crypto.js",
    "assets/aes-cbc-hmac.js",
    "assets/api-client.js",
    "assets/api-errors.js",
    "assets/app.js",
    "assets/auth-kdf.js",
    "assets/auth-protocol.js",
    "assets/auth-request.js",
    "assets/auth-state.js",
    "assets/authenticated-api.js",
    "assets/client-sdk.js",
    "assets/crypto-boundary.js",
    "assets/enc-string.js",
    "assets/feedback.css",
    "assets/glaze.css",
    "assets/goreevault-mark.svg",
    "assets/identity-protocol.js",
    "assets/master-key-crypto.js",
    "assets/runtime-config.js",
    "assets/server-config.js",
    "assets/session-state.js",
    "assets/sync-client.js",
    "assets/sync-protocol.js",
    "assets/theme-init.js",
    "assets/token-state.js",
    "assets/unlock-coordinator.js",
    "assets/vault-state.js",
)


def file_digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256(path: Path) -> str:
    return file_digest(path, "sha256")


def source_created_at(source_date_epoch: int) -> str:
    if source_date_epoch < 0:
        raise ValueError("source date epoch must be zero or greater")
    return datetime.fromtimestamp(source_date_epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def spdx_file_id(relative: str) -> str:
    return f"SPDXRef-File-{hashlib.sha256(relative.encode('utf-8')).hexdigest()[:20]}"


def verification_code(sha1_values: list[str]) -> str:
    combined = "".join(sorted(sha1_values))
    return hashlib.sha1(combined.encode("ascii")).hexdigest()


def build_spdx(out: Path, source_revision: str, source_date_epoch: int, files: list[dict[str, object]]) -> dict[str, object]:
    spdx_files: list[dict[str, object]] = []
    relationships: list[dict[str, str]] = [{
        "spdxElementId": "SPDXRef-DOCUMENT",
        "relationshipType": "DESCRIBES",
        "relatedSpdxElement": "SPDXRef-Package-GoreeVault-Web",
    }]
    sha1_values: list[str] = []

    for entry in files:
        relative = str(entry["path"])
        target = out / relative
        sha1_value = file_digest(target, "sha1")
        sha1_values.append(sha1_value)
        file_id = spdx_file_id(relative)
        spdx_files.append({
            "fileName": f"./{relative}",
            "SPDXID": file_id,
            "checksums": [
                {"algorithm": "SHA1", "checksumValue": sha1_value},
                {"algorithm": "SHA256", "checksumValue": str(entry["sha256"])},
            ],
            "licenseConcluded": "NOASSERTION",
            "licenseInfoInFiles": ["NOASSERTION"],
            "copyrightText": "NOASSERTION",
        })
        relationships.append({
            "spdxElementId": "SPDXRef-Package-GoreeVault-Web",
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": file_id,
        })

    namespace_revision = quote(source_revision, safe="")
    return {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"GoreeVault-Web-{source_revision}",
        "documentNamespace": f"https://goreecloud.com/spdx/goreevault-web/{namespace_revision}",
        "creationInfo": {
            "created": source_created_at(source_date_epoch),
            "creators": ["Tool: GoreeVault Web deterministic release builder"],
        },
        "packages": [{
            "name": "GoreeVault Web",
            "SPDXID": "SPDXRef-Package-GoreeVault-Web",
            "versionInfo": "0.0.0-prealpha",
            "packageFileName": "./",
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": True,
            "packageVerificationCode": {
                "packageVerificationCodeValue": verification_code(sha1_values),
            },
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "primaryPackagePurpose": "APPLICATION",
        }],
        "files": spdx_files,
        "relationships": relationships,
    }


def build(out: Path, source_revision: str, source_date_epoch: int = 0) -> dict[str, object]:
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

    sbom = build_spdx(out, source_revision, source_date_epoch, files)
    sbom_path = out / SBOM_NAME
    sbom_path.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest: dict[str, object] = {
        "schema": 2,
        "product": "GoreeVault Web",
        "channel": "pre-alpha",
        "sourceRevision": source_revision,
        "sourceDateEpoch": source_date_epoch,
        "runtimeDependencies": [],
        "files": files,
        "sbom": {
            "format": SPDX_VERSION,
            "path": SBOM_NAME,
            "sha256": sha256(sbom_path),
            "bytes": sbom_path.stat().st_size,
        },
    }
    manifest_path = out / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--source-revision", default="unverified-local")
    parser.add_argument(
        "--source-date-epoch",
        type=int,
        default=0,
        help="UTC source timestamp used for deterministic SPDX creation metadata.",
    )
    args = parser.parse_args()
    manifest = build(args.out, args.source_revision, args.source_date_epoch)
    print(
        f"Built {len(manifest['files'])} GoreeVault Web release files plus {SBOM_NAME} at {args.out}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
