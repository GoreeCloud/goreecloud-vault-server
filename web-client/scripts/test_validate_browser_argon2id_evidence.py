#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("validate_browser_argon2id_evidence.py")
spec = importlib.util.spec_from_file_location("browser_evidence", MODULE_PATH)
assert spec and spec.loader
browser_evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(browser_evidence)


def valid_evidence() -> dict[str, object]:
    return {
        "schema": 1,
        "evidenceType": "goreevault-web-argon2id-real-browser",
        "sourceRevision": "a" * 40,
        "candidateManifestSha256": "b" * 64,
        "browser": {
            "name": "Firefox",
            "version": "143.0",
            "engine": "gecko",
            "os": "Linux",
            "architecture": "x86_64",
        },
        "servedOrigin": "https://vault-validation.goreecloud.test",
        "artifacts": {
            "javascriptPath": "goreevault_web_argon2id_core.js",
            "javascriptSha256": "c" * 64,
            "wasmPath": "goreevault_web_argon2id_core_bg.wasm",
            "wasmSha256": "d" * 64,
        },
        "execution": {
            "realBrowserExecuted": True,
            "generatedBindingsLoaded": True,
            "wasmInitialized": True,
            "bitwardenVectorPassed": True,
            "authenticationMaterialMatched": True,
            "sameOriginLoadObserved": True,
            "providerRegistrationWasExplicit": True,
        },
        "csp": {"effectivePolicy": "default-src 'self'; script-src 'self'; object-src 'none'", "violations": []},
        "performance": {"samples": 5, "deriveMsP50": 120.0, "deriveMsP95": 150.0, "deriveMsMax": 175.0},
        "memory": {"method": "browser performance memory observation", "beforeBytes": 100, "afterBytes": 110, "peakBytes": 180, "leakSuspected": False},
        "approvals": {
            "credentialProcessingApproved": False,
            "productionReleaseApproved": False,
            "stablePromotionApproved": False,
        },
        "accepted": True,
    }


class BrowserEvidenceTests(unittest.TestCase):
    def test_valid_real_browser_evidence_passes(self) -> None:
        browser_evidence.validate_evidence(valid_evidence())

    def test_synthetic_browser_flag_fails(self) -> None:
        evidence = valid_evidence()
        evidence["execution"]["realBrowserExecuted"] = False
        with self.assertRaises(browser_evidence.EvidenceError):
            browser_evidence.validate_evidence(evidence)

    def test_production_approval_fails(self) -> None:
        evidence = valid_evidence()
        evidence["approvals"]["productionReleaseApproved"] = True
        with self.assertRaises(browser_evidence.EvidenceError):
            browser_evidence.validate_evidence(evidence)

    def test_csp_violation_fails(self) -> None:
        evidence = valid_evidence()
        evidence["csp"]["violations"] = ["blocked wasm"]
        with self.assertRaises(browser_evidence.EvidenceError):
            browser_evidence.validate_evidence(evidence)

    def test_http_origin_fails(self) -> None:
        evidence = valid_evidence()
        evidence["servedOrigin"] = "http://localhost:8080"
        with self.assertRaises(browser_evidence.EvidenceError):
            browser_evidence.validate_evidence(evidence)

    def test_performance_ordering_fails(self) -> None:
        evidence = valid_evidence()
        evidence["performance"]["deriveMsP95"] = 90
        with self.assertRaises(browser_evidence.EvidenceError):
            browser_evidence.validate_evidence(evidence)

    def test_memory_leak_flag_fails(self) -> None:
        evidence = valid_evidence()
        evidence["memory"]["leakSuspected"] = True
        with self.assertRaises(browser_evidence.EvidenceError):
            browser_evidence.validate_evidence(evidence)


if __name__ == "__main__":
    unittest.main()
