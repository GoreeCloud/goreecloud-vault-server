#!/usr/bin/env python3
"""Project validated GoreeCloud Vault Server Stable evidence into minimized capability evidence.

This companion intentionally delegates evidence validity to the canonical
validate-stable-evidence.py validator. It does not inspect credentials, vault
contents, reviewer identities, or raw evidence references, and it does not turn
a validated candidate bundle into a runtime/production-deployment claim.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

VALIDATOR_PATH = Path(__file__).with_name("validate-stable-evidence.py")
SPEC = importlib.util.spec_from_file_location("goreevault_stable_evidence", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator from {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def project_capability_evidence(
    data: Any,
    *,
    expected_source_sha: str,
    expected_rc_tag: str,
    expected_manifest_digest: str,
) -> dict[str, Any]:
    """Validate one exact candidate and return only bounded service evidence."""
    VALIDATOR.validate_evidence(
        data,
        expected_source_sha=expected_source_sha,
        expected_rc_tag=expected_rc_tag,
        expected_manifest_digest=expected_manifest_digest,
        allow_placeholders=False,
    )

    rc = data["rc"]
    return {
        "schema_version": 1,
        "product": "GoreeCloud Vault Server",
        "service": "vault",
        "validation_scope": "stable-evidence-exact-pinned",
        "capabilities": [
            {
                "id": "vault.secrets",
                "contract_version": "1",
                "authoritative": True,
                "current": True,
                "stable_evidence_accepted": True,
                "production_accepted": False,
            }
        ],
        "candidate": {
            "tag": rc["tag"],
            "source_sha": rc["source_sha"],
            "manifest_digest": rc["manifest_digest"],
        },
        "contains_user_content": False,
        "credentials_exposed": False,
        "runtime_deployment_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="Path to goreevault-stable-evidence.json")
    parser.add_argument("--expected-source-sha", required=True)
    parser.add_argument("--expected-rc-tag", required=True)
    parser.add_argument("--expected-manifest-digest", required=True)
    args = parser.parse_args()

    try:
        raw = args.evidence.read_text(encoding="utf-8")
        data = VALIDATOR.load_json_strict(raw)
        projection = project_capability_evidence(
            data,
            expected_source_sha=args.expected_source_sha,
            expected_rc_tag=args.expected_rc_tag,
            expected_manifest_digest=args.expected_manifest_digest,
        )
    except (OSError, json.JSONDecodeError, VALIDATOR.EvidenceError) as exc:
        print(f"Stable capability evidence projection failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(projection, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
