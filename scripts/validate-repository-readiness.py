#!/usr/bin/env python3
"""Validate GoreeVault repository identity and production-readiness contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "README.md",
    "GOREVAULT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/GLAZE-UI.md",
    "docs/OPEN-READINESS-BLOCKERS.md",
    "docs/PRODUCTION-DEPLOYMENT.md",
    "docs/PRODUCTION-READINESS.md",
    "docs/REPOSITORY-STRUCTURE.md",
    "docs/SECURITY-MODEL.md",
    "docs/STABLE-EVIDENCE.md",
    "docs/UPSTREAM.md",
    "scripts/validate-glaze-ui.py",
    "scripts/validate-production-deployment.sh",
    "scripts/validate-stable-evidence.py",
}


class ReadinessError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReadinessError(message)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def validate_files() -> None:
    missing = sorted(path for path in REQUIRED_FILES if not (ROOT / path).is_file())
    require(not missing, f"missing required GoreeVault repository files: {', '.join(missing)}")


def validate_readme() -> None:
    text = read("README.md")
    require(text.startswith("# GoreeVault Server\n"), "README.md must begin with the GoreeVault Server identity")
    require("Vaultwarden Logo" not in text, "README.md must not present the upstream Vaultwarden logo as GoreeVault identity")
    require("vaultwarden/server:latest" not in text, "README.md must not recommend mutable upstream latest images")
    require("goreevault-server:latest" not in text, "README.md must not recommend a mutable GoreeVault latest image")
    require("docs/REPOSITORY-STRUCTURE.md" in text, "README.md must link the repository structure contract")
    require("multi-user" in text.lower(), "README.md must document GoreeVault multi-user readiness")
    require("Glaze UI" in text, "README.md must document Glaze UI")
    require("not approved" in text.lower(), "README.md must state the current non-Stable production boundary")


def validate_codeowners() -> None:
    text = read(".github/CODEOWNERS")
    required = {
        "/README.md @GoreeCloud",
        "/GOREVAULT.md @GoreeCloud",
        "/docs/** @GoreeCloud",
        "/src/** @GoreeCloud",
        "/tests/** @GoreeCloud",
        "/scripts/** @GoreeCloud",
        "/deploy/** @GoreeCloud",
    }
    missing = sorted(line for line in required if line not in text)
    require(not missing, f"CODEOWNERS is missing GoreeCloud review ownership: {', '.join(missing)}")


def validate_security_reporting() -> None:
    text = read("SECURITY.md")
    require("security@goreecloud.com" in text, "SECURITY.md must provide the private GoreeCloud security contact")
    require(
        "https://www.goreecloud.com/security.html" in text,
        "SECURITY.md must reference the canonical public GoreeCloud security policy",
    )
    require(
        "ordinary GitHub Issues disabled" in text,
        "SECURITY.md must document that ordinary GitHub Issues are not a reporting fallback",
    )
    require(
        "public issue is **not** the security-reporting fallback" in text,
        "SECURITY.md must reject public issue disclosure as the fallback path",
    )
    require(
        "private vulnerability reporting" in text.lower(),
        "SECURITY.md must prefer GitHub private vulnerability reporting when available",
    )


def validate_goreecloud_gates() -> None:
    goreevault = read("GOREVAULT.md")
    readiness = read("docs/PRODUCTION-READINESS.md")
    glaze = read("docs/GLAZE-UI.md")
    stable = read("docs/STABLE-EVIDENCE.md")
    blockers = read("docs/OPEN-READINESS-BLOCKERS.md")

    for name, text in {
        "GOREVAULT.md": goreevault,
        "docs/PRODUCTION-READINESS.md": readiness,
    }.items():
        lower = text.lower()
        require("multi-user" in lower, f"{name} must document the mandatory multi-user gate")
        require("security" in lower, f"{name} must document the mandatory security gate")
        require("glaze ui" in lower, f"{name} must document the mandatory Glaze UI gate")

    require(
        "temporary development divergence" in glaze,
        "docs/GLAZE-UI.md must classify the upstream browser vault as temporary development divergence",
    )
    require(
        "No production Glaze UI exception is approved" in glaze,
        "docs/GLAZE-UI.md must not silently approve an upstream styling exception",
    )
    require(
        "Stable is therefore blocked" in readiness,
        "docs/PRODUCTION-READINESS.md must explicitly block Stable while product-wide Glaze is incomplete",
    )
    require(
        "Schema version 2" in stable,
        "docs/STABLE-EVIDENCE.md must use the multi-user/Glaze-aware Stable evidence schema",
    )
    for blocker in (
        "GitHub repository governance",
        "Real supported-client matrix",
        "Real WebAuthn/passkey path",
        "Target-environment production rehearsal",
        "Product-wide Glaze UI ownership",
        "Exact-RC Stable evidence",
    ):
        require(blocker in blockers, f"open readiness tracker is missing blocker: {blocker}")
    require("Status:** Stable blocked" in blockers, "open readiness tracker must preserve the Stable-blocked state")


def validate_stable_template() -> None:
    text = read("docs/stable-evidence.example.json")
    required_tokens = {
        '"schema_version": 2',
        '"multi_user"',
        '"glaze_ui"',
        '"product_wide_conformance": true',
        '"primary_browser_vault_goreecloud_owned": true',
        '"private_vault_isolation": true',
    }
    missing = sorted(token for token in required_tokens if token not in text)
    require(not missing, f"Stable evidence template is missing required readiness fields: {', '.join(missing)}")


def validate_mutable_production_examples() -> None:
    paths = [
        "README.md",
        "docs/PRODUCTION-DEPLOYMENT.md",
        "deploy/compose.production.yaml",
        "deploy/.env.production.example",
    ]
    mutable_image = re.compile(r"(?:image\s*:\s*|docker\s+(?:pull|run)\s+)[^\s]+:latest\b", re.IGNORECASE)
    for path in paths:
        text = read(path)
        match = mutable_image.search(text)
        require(match is None, f"{path} contains a mutable :latest production image example: {match.group(0) if match else ''}")


def main() -> int:
    try:
        validate_files()
        validate_readme()
        validate_codeowners()
        validate_security_reporting()
        validate_goreecloud_gates()
        validate_stable_template()
        validate_mutable_production_examples()
    except (OSError, UnicodeError, ReadinessError) as exc:
        print(f"Repository readiness validation failed: {exc}", file=sys.stderr)
        return 1

    print("GoreeVault repository readiness validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
