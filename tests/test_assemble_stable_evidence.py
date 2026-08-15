#!/usr/bin/env python3
"""Unit tests for scripts/assemble-stable-evidence.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "assemble-stable-evidence.py"
SPEC = importlib.util.spec_from_file_location("assemble_stable_evidence", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
assembler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembler)
validator = assembler.load_validator()


def concrete_template() -> dict:
    raw = (ROOT / "docs" / "stable-evidence.example.json").read_text(encoding="utf-8")
    data = validator.load_json_strict(raw)

    counter = 0

    def replace(value):
        nonlocal counter
        if isinstance(value, dict):
            return {key: replace(child) for key, child in value.items()}
        if isinstance(value, list):
            return [replace(child) for child in value]
        if isinstance(value, str) and "REPLACE_ME" in value:
            if "@sha256:" in value:
                return value.replace("REPLACE_ME_", "", 1)
            counter += 1
            return f"synthetic-evidence-{counter}"
        return value

    concrete = replace(data)
    validator.validate_evidence(
        concrete,
        expected_source_sha=concrete["rc"]["source_sha"],
        expected_rc_tag=concrete["rc"]["tag"],
        expected_manifest_digest=concrete["rc"]["manifest_digest"],
        allow_placeholders=False,
    )
    return concrete


def section_map(evidence: dict) -> dict:
    return {
        "rc": evidence["rc"],
        "multi_user": evidence["multi_user"],
        "clients": evidence["clients"],
        "webauthn": evidence["webauthn"],
        "glaze_ui": evidence["glaze_ui"],
        "target_environment": evidence["target_environment"],
        "governance": evidence["governance"],
        "approvals": evidence["approvals"],
    }


class StableEvidenceAssemblerTests(unittest.TestCase):
    def test_assemble_validates_exact_candidate(self) -> None:
        source = concrete_template()
        assembled = assembler.assemble(
            section_map(source),
            assembled_at="2026-08-15T06:30:00-05:00",
            expected_source_sha=source["rc"]["source_sha"],
            expected_rc_tag=source["rc"]["tag"],
            expected_manifest_digest=source["rc"]["manifest_digest"],
            validator=validator,
        )
        self.assertEqual(assembled["schema_version"], 2)
        self.assertEqual(assembled["rc"], source["rc"])
        self.assertEqual(assembled["target_environment"], source["target_environment"])
        self.assertEqual(assembled["collected_at"], "2026-08-15T06:30:00-05:00")

    def test_assemble_rejects_wrong_expected_source(self) -> None:
        source = concrete_template()
        with self.assertRaises(assembler.AssemblyError):
            assembler.assemble(
                section_map(source),
                assembled_at="2026-08-15T06:30:00-05:00",
                expected_source_sha="a" * 40,
                expected_rc_tag=source["rc"]["tag"],
                expected_manifest_digest=source["rc"]["manifest_digest"],
                validator=validator,
            )

    def test_assemble_rejects_unknown_section_field(self) -> None:
        source = concrete_template()
        sections = section_map(source)
        sections["governance"] = dict(sections["governance"])
        sections["governance"]["unexpected_token"] = "do-not-store-this"
        with self.assertRaises(assembler.AssemblyError):
            assembler.assemble(
                sections,
                assembled_at="2026-08-15T06:30:00-05:00",
                expected_source_sha=source["rc"]["source_sha"],
                expected_rc_tag=source["rc"]["tag"],
                expected_manifest_digest=source["rc"]["manifest_digest"],
                validator=validator,
            )

    def test_read_section_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "section.json"
            path.write_text('{"result":"pass","result":"fail"}\n', encoding="utf-8")
            with self.assertRaises(assembler.AssemblyError):
                assembler.read_section(path, validator)

    def test_write_is_mode_0600_and_refuses_implicit_overwrite(self) -> None:
        source = concrete_template()
        assembled = assembler.assemble(
            section_map(source),
            assembled_at="2026-08-15T06:30:00-05:00",
            expected_source_sha=source["rc"]["source_sha"],
            expected_rc_tag=source["rc"]["tag"],
            expected_manifest_digest=source["rc"]["manifest_digest"],
            validator=validator,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "goreevault-stable-evidence.json"
            assembler.write_evidence(path, assembled, force=False)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            written = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(written["rc"]["source_sha"], source["rc"]["source_sha"])

            with self.assertRaises(assembler.AssemblyError):
                assembler.write_evidence(path, assembled, force=False)

            assembler.write_evidence(path, assembled, force=True)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_write_refuses_symbolic_link(self) -> None:
        source = concrete_template()
        assembled = assembler.assemble(
            section_map(source),
            assembled_at="2026-08-15T06:30:00-05:00",
            expected_source_sha=source["rc"]["source_sha"],
            expected_rc_tag=source["rc"]["tag"],
            expected_manifest_digest=source["rc"]["manifest_digest"],
            validator=validator,
        )

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.json"
            target.write_text("{}\n", encoding="utf-8")
            link = Path(directory) / "evidence.json"
            link.symlink_to(target)
            with self.assertRaises(assembler.AssemblyError):
                assembler.write_evidence(link, assembled, force=True)


if __name__ == "__main__":
    unittest.main()
