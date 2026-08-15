#!/usr/bin/env python3
"""Unit tests for scripts/collect-target-evidence.py.

These tests exercise the collector's fail-closed pure checks without requiring a
Docker daemon, production environment, network access, or real credentials.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "collect-target-evidence.py"
SPEC = importlib.util.spec_from_file_location("collect_target_evidence", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


def server_fixture(*, host_ip: str = "127.0.0.1", user: str = "10001:10001") -> dict:
    return {
        "Config": {
            "User": user,
            "Image": "ghcr.io/goreecloud/goreevault-server@sha256:" + "2" * 64,
            "Env": ["SIGNUPS_ALLOWED=false", "ADMIN_TOKEN="],
        },
        "HostConfig": {
            "ReadonlyRootfs": True,
            "CapDrop": ["ALL"],
            "SecurityOpt": ["no-new-privileges:true"],
        },
        "NetworkSettings": {
            "Ports": {
                "80/tcp": [{"HostIp": host_ip, "HostPort": "8080"}],
            }
        },
    }


def postgres_fixture(*, published: bool = False) -> dict:
    return {
        "Config": {
            "Image": "docker.io/library/postgres@sha256:" + "3" * 64,
        },
        "NetworkSettings": {
            "Ports": {
                "5432/tcp": ([{"HostIp": "127.0.0.1", "HostPort": "5432"}] if published else None),
            }
        },
    }


class TargetEvidenceCollectorTests(unittest.TestCase):
    def test_digest_pinning(self) -> None:
        self.assertTrue(
            collector.image_is_digest_pinned(
                "ghcr.io/goreecloud/goreevault-server@sha256:" + "a" * 64
            )
        )
        self.assertFalse(collector.image_is_digest_pinned("ghcr.io/goreecloud/goreevault-server:latest"))
        self.assertFalse(collector.image_is_digest_pinned("ghcr.io/goreecloud/goreevault-server:v0.3.0"))

    def test_backend_requires_loopback_publication(self) -> None:
        self.assertTrue(collector.backend_is_loopback_only(server_fixture()))
        self.assertFalse(collector.backend_is_loopback_only(server_fixture(host_ip="0.0.0.0")))
        no_ports = server_fixture()
        no_ports["NetworkSettings"]["Ports"] = {"80/tcp": None}
        self.assertFalse(collector.backend_is_loopback_only(no_ports))

    def test_postgres_must_not_publish_host_port(self) -> None:
        self.assertTrue(collector.postgres_is_internal_only(postgres_fixture()))
        self.assertFalse(collector.postgres_is_internal_only(postgres_fixture(published=True)))

    def test_runtime_hardening_checks(self) -> None:
        server = server_fixture()
        self.assertTrue(collector.server_is_non_root(server))
        self.assertTrue(collector.root_filesystem_is_read_only(server))
        self.assertTrue(collector.capabilities_are_dropped(server))
        self.assertTrue(collector.no_new_privileges_enabled(server))
        self.assertTrue(collector.registration_is_closed(server))
        self.assertTrue(collector.admin_is_disabled(server))

        root_server = server_fixture(user="0:0")
        self.assertFalse(collector.server_is_non_root(root_server))

    def test_env_file_rejects_group_or_world_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "production.env"
            path.write_text(
                "GOREVAULT_IMAGE=ghcr.io/goreecloud/goreevault-server@sha256:" + "2" * 64 + "\n",
                encoding="utf-8",
            )
            path.chmod(0o600)
            values = collector.parse_env_file(path)
            self.assertIn("GOREVAULT_IMAGE", values)

            path.chmod(0o644)
            with self.assertRaises(collector.EvidenceError):
                collector.parse_env_file(path)

    def test_references_reject_placeholders_and_multiline_values(self) -> None:
        self.assertEqual(collector.validate_reference("backup", "backup-job-20260815"), "backup-job-20260815")
        with self.assertRaises(collector.EvidenceError):
            collector.validate_reference("backup", "REPLACE_ME")
        with self.assertRaises(collector.EvidenceError):
            collector.validate_reference("backup", "first\nsecond")


if __name__ == "__main__":
    unittest.main()
