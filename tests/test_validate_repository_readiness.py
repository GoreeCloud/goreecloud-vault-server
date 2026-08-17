#!/usr/bin/env python3
"""Unit tests for GoreeVault repository-readiness policy validation.

The tests redirect the validator's repository root into isolated temporary
fixtures so fail-closed policy behavior is exercised without modifying real
project files.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate-repository-readiness.py"
SPEC = importlib.util.spec_from_file_location("goreevault_repository_readiness", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator from {MODULE_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class RepositoryReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.original_root = VALIDATOR.ROOT
        VALIDATOR.ROOT = self.root
        self.addCleanup(setattr, VALIDATOR, "ROOT", self.original_root)

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def test_codeowners_requires_core_goreecloud_ownership(self) -> None:
        self.write(".github/CODEOWNERS", "/README.md @GoreeCloud\n")
        with self.assertRaisesRegex(VALIDATOR.ReadinessError, "CODEOWNERS is missing"):
            VALIDATOR.validate_codeowners()

    def test_codeowners_accepts_required_protected_surfaces(self) -> None:
        required = [
            "/README.md @GoreeCloud",
            "/GOREVAULT.md @GoreeCloud",
            "/docs/** @GoreeCloud",
            "/src/** @GoreeCloud",
            "/tests/** @GoreeCloud",
            "/scripts/** @GoreeCloud",
            "/deploy/** @GoreeCloud",
        ]
        self.write(".github/CODEOWNERS", "\n".join(required) + "\n")
        VALIDATOR.validate_codeowners()

    def test_readme_rejects_upstream_identity(self) -> None:
        self.write("README.md", "# Vaultwarden\nVaultwarden Logo\n")
        with self.assertRaisesRegex(VALIDATOR.ReadinessError, "GoreeVault Server identity"):
            VALIDATOR.validate_readme()

    def test_security_reporting_requires_private_goreecloud_path(self) -> None:
        self.write("SECURITY.md", "Please open a public issue.\n")
        with self.assertRaisesRegex(VALIDATOR.ReadinessError, "private GoreeCloud security contact"):
            VALIDATOR.validate_security_reporting()

    def test_mutable_latest_production_image_is_rejected(self) -> None:
        self.write("README.md", "docker run ghcr.io/goreecloud/goreevault-server:latest\n")
        self.write("docs/PRODUCTION-DEPLOYMENT.md", "immutable deployment only\n")
        self.write("deploy/compose.production.yaml", "services: {}\n")
        self.write("deploy/.env.production.example", "IMAGE=example@sha256:" + "a" * 64 + "\n")
        with self.assertRaisesRegex(VALIDATOR.ReadinessError, "mutable :latest production image"):
            VALIDATOR.validate_mutable_production_examples()

    def test_immutable_production_examples_pass(self) -> None:
        digest = "sha256:" + "a" * 64
        self.write("README.md", f"docker pull ghcr.io/goreecloud/goreevault-server@{digest}\n")
        self.write("docs/PRODUCTION-DEPLOYMENT.md", f"docker run ghcr.io/goreecloud/goreevault-server@{digest}\n")
        self.write("deploy/compose.production.yaml", f"services:\n  app:\n    image: ghcr.io/goreecloud/goreevault-server@{digest}\n")
        self.write("deploy/.env.production.example", f"GOREEVAULT_IMAGE=ghcr.io/goreecloud/goreevault-server@{digest}\n")
        VALIDATOR.validate_mutable_production_examples()

    def test_open_blocker_tracker_must_preserve_all_stable_gates(self) -> None:
        self.write("GOREVAULT.md", "multi-user security Glaze UI\n")
        self.write("docs/PRODUCTION-READINESS.md", "multi-user security Glaze UI\nStable is therefore blocked\n")
        self.write("docs/GLAZE-UI.md", "temporary development divergence\nNo production Glaze UI exception is approved\n")
        self.write("docs/STABLE-EVIDENCE.md", "Schema version 2\n")
        self.write("docs/OPEN-READINESS-BLOCKERS.md", "Status:** Stable blocked\nGitHub repository governance\n")
        with self.assertRaisesRegex(VALIDATOR.ReadinessError, "open readiness tracker is missing blocker"):
            VALIDATOR.validate_goreecloud_gates()

    def test_stable_template_requires_multi_user_and_glaze_fields(self) -> None:
        self.write("docs/stable-evidence.example.json", '{"schema_version": 2, "multi_user": {}}\n')
        with self.assertRaisesRegex(VALIDATOR.ReadinessError, "Stable evidence template is missing"):
            VALIDATOR.validate_stable_template()


if __name__ == "__main__":
    unittest.main()
