#!/usr/bin/env python3
"""Unit tests for scripts/collect-target-evidence.py.

These tests exercise the collector's fail-closed checks without requiring a
Docker daemon, target environment, network access, or real credentials.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "collect-target-evidence.py"
SPEC = importlib.util.spec_from_file_location("collect_target_evidence", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


GOREVAULT_DIGEST = "sha256:" + "2" * 64
POSTGRES_DIGEST = "sha256:" + "3" * 64
PREVIOUS_DIGEST = "sha256:" + "4" * 64
GOREVAULT_IMAGE = "ghcr.io/goreecloud/goreevault-server@" + GOREVAULT_DIGEST
POSTGRES_IMAGE = "docker.io/library/postgres@" + POSTGRES_DIGEST
PREVIOUS_IMAGE = "ghcr.io/goreecloud/goreevault-server@" + PREVIOUS_DIGEST


def server_fixture(
    *,
    host_ip: str = "127.0.0.1",
    user: str = "10001:10001",
    running: bool = True,
    healthy: bool = True,
) -> dict:
    return {
        "Config": {
            "User": user,
            "Image": GOREVAULT_IMAGE,
            "Env": ["SIGNUPS_ALLOWED=false", "ADMIN_TOKEN="],
        },
        "HostConfig": {
            "ReadonlyRootfs": True,
            "CapDrop": ["ALL"],
            "SecurityOpt": ["no-new-privileges:true"],
        },
        "State": {
            "Running": running,
            "Health": {"Status": "healthy" if healthy else "unhealthy"},
        },
        "NetworkSettings": {
            "Ports": {
                "80/tcp": [{"HostIp": host_ip, "HostPort": "8080"}],
            }
        },
    }


def postgres_fixture(*, published: bool = False, running: bool = True, healthy: bool = True) -> dict:
    return {
        "Config": {
            "Image": POSTGRES_IMAGE,
        },
        "State": {
            "Running": running,
            "Health": {"Status": "healthy" if healthy else "unhealthy"},
        },
        "NetworkSettings": {
            "Ports": {
                "5432/tcp": ([{"HostIp": "127.0.0.1", "HostPort": "5432"}] if published else None),
            }
        },
    }


def args_fixture(env_file: Path, **overrides) -> SimpleNamespace:
    values = {
        "env_file": env_file,
        "repository_root": ROOT,
        "compose_file": Path("deploy/compose.production.yaml"),
        "goreevault_container": "goreevault-server",
        "postgres_container": "goreevault-postgres",
        "origin": collector.EXPECTED_ORIGIN,
        "expected_manifest_digest": GOREVAULT_DIGEST,
        "previous_known_good_image": PREVIOUS_IMAGE,
        "backup_reference": "backup-job-20260815",
        "rollback_reference": "rollback-rehearsal-20260815",
        "timezone": "America/Chicago",
        "http_timeout": 10,
        "output": None,
        "reverse_proxy_https_wss": True,
        "backup_created": True,
        "restore_rehearsed": True,
        "rollback_recorded": True,
        "monitoring_verified": True,
        "logs_reviewed_for_sensitive_data": True,
        "netbird_path_verified": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def write_env(directory: str, *, goreevault_image: str = GOREVAULT_IMAGE) -> Path:
    path = Path(directory) / "production.env"
    path.write_text(
        f"GOREVAULT_IMAGE={goreevault_image}\n"
        f"POSTGRES_IMAGE={POSTGRES_IMAGE}\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    return path


class TargetEvidenceCollectorTests(unittest.TestCase):
    def test_digest_pinning(self) -> None:
        self.assertTrue(collector.image_is_digest_pinned(GOREVAULT_IMAGE))
        self.assertEqual(collector.image_digest(GOREVAULT_IMAGE), GOREVAULT_DIGEST)
        self.assertFalse(collector.image_is_digest_pinned("ghcr.io/goreecloud/goreevault-server:latest"))
        self.assertFalse(collector.image_is_digest_pinned("ghcr.io/goreecloud/goreevault-server:v0.3.0"))
        self.assertEqual(collector.image_digest("ghcr.io/goreecloud/goreevault-server:latest"), "")

    def test_container_state_requires_running_and_healthy(self) -> None:
        server = server_fixture()
        self.assertTrue(collector.container_is_running(server))
        self.assertTrue(collector.container_is_healthy(server))
        self.assertFalse(collector.container_is_running(server_fixture(running=False)))
        self.assertFalse(collector.container_is_healthy(server_fixture(healthy=False)))

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

        self.assertFalse(collector.server_is_non_root(server_fixture(user="0:0")))
        self.assertFalse(collector.server_is_non_root(server_fixture(user="vaultwarden")))
        self.assertFalse(collector.server_is_non_root(server_fixture(user="10001:0")))

    def test_env_file_rejects_group_or_world_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_env(directory)
            values = collector.parse_env_file(path)
            self.assertEqual(values["GOREVAULT_IMAGE"], GOREVAULT_IMAGE)

            path.chmod(0o644)
            with self.assertRaises(collector.EvidenceError):
                collector.parse_env_file(path)

    def test_references_reject_placeholders_and_multiline_values(self) -> None:
        self.assertEqual(collector.validate_reference("backup", "backup-job-20260815"), "backup-job-20260815")
        with self.assertRaises(collector.EvidenceError):
            collector.validate_reference("backup", "REPLACE_ME")
        with self.assertRaises(collector.EvidenceError):
            collector.validate_reference("backup", "first\nsecond")

    def test_collect_builds_exact_non_secret_target_environment_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = write_env(directory)
            args = args_fixture(env_file)
            with (
                patch.object(collector, "verify_contract") as verify_contract,
                patch.object(collector, "verify_compose_renders") as verify_compose,
                patch.object(collector, "verify_https_origin") as verify_https,
                patch.object(
                    collector,
                    "inspect_container",
                    side_effect=[server_fixture(), postgres_fixture()],
                ) as inspect_container,
            ):
                evidence = collector.collect(args)

            verify_contract.assert_called_once()
            verify_compose.assert_called_once()
            verify_https.assert_called_once_with(collector.EXPECTED_ORIGIN, 10)
            self.assertEqual(
                [call.args[0] for call in inspect_container.call_args_list],
                ["goreevault-server", "goreevault-postgres"],
            )
            self.assertEqual(evidence["result"], "pass")
            self.assertEqual(evidence["origin"], collector.EXPECTED_ORIGIN)
            self.assertEqual(evidence["goreevault_image"], GOREVAULT_IMAGE)
            self.assertEqual(evidence["previous_known_good_image"], PREVIOUS_IMAGE)
            self.assertEqual(evidence["backup_reference"], "backup-job-20260815")
            self.assertEqual(evidence["rollback_reference"], "rollback-rehearsal-20260815")
            self.assertTrue(evidence["backend_loopback_only"])
            self.assertTrue(evidence["restore_rehearsed"])
            self.assertNotIn("POSTGRES_PASSWORD", evidence)
            self.assertNotIn("environment", evidence)

    def test_collect_rejects_missing_operator_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = write_env(directory)
            args = args_fixture(env_file, monitoring_verified=False)
            with self.assertRaises(collector.EvidenceError):
                collector.collect(args)

    def test_collect_rejects_wrong_rc_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wrong_image = "ghcr.io/goreecloud/goreevault-server@sha256:" + "5" * 64
            env_file = write_env(directory, goreevault_image=wrong_image)
            args = args_fixture(env_file)
            with self.assertRaises(collector.EvidenceError):
                collector.collect(args)


if __name__ == "__main__":
    unittest.main()
