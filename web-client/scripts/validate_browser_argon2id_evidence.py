#!/usr/bin/env python3
"""Validate real-browser GoreeVault Web Argon2id acceptance evidence.

This validator is intentionally fail-closed. It validates evidence produced by a real
browser run against exact candidate artifacts; it does not execute a browser and CI
success must not be interpreted as browser acceptance.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_ENGINES = {"blink", "gecko", "webkit"}


class EvidenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def require_nonempty_string(value: object, name: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{name} must be a non-empty string")
    return value.strip()


def require_sha256(value: object, name: str) -> str:
    text = require_nonempty_string(value, name)
    require(bool(SHA256_RE.fullmatch(text)), f"{name} must be a lowercase SHA-256 digest")
    return text


def require_git_sha(value: object, name: str) -> str:
    text = require_nonempty_string(value, name)
    require(bool(GIT_SHA_RE.fullmatch(text)), f"{name} must be a full lowercase Git SHA")
    return text


def validate_positive_number(value: object, name: str, *, allow_zero: bool = False) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{name} must be numeric")
    number = float(value)
    require(number >= 0 if allow_zero else number > 0, f"{name} must be {'zero or greater' if allow_zero else 'greater than zero'}")
    return number


def validate_evidence(data: object) -> dict[str, object]:
    require(isinstance(data, dict), "evidence root must be an object")
    evidence = data

    require(evidence.get("schema") == 1, "schema must equal 1")
    require(evidence.get("evidenceType") == "goreevault-web-argon2id-real-browser", "unexpected evidenceType")
    require_git_sha(evidence.get("sourceRevision"), "sourceRevision")
    require_sha256(evidence.get("candidateManifestSha256"), "candidateManifestSha256")

    browser = evidence.get("browser")
    require(isinstance(browser, dict), "browser must be an object")
    require_nonempty_string(browser.get("name"), "browser.name")
    require_nonempty_string(browser.get("version"), "browser.version")
    engine = require_nonempty_string(browser.get("engine"), "browser.engine").lower()
    require(engine in ALLOWED_ENGINES, f"browser.engine must be one of {sorted(ALLOWED_ENGINES)}")
    require_nonempty_string(browser.get("os"), "browser.os")
    require_nonempty_string(browser.get("architecture"), "browser.architecture")

    origin = require_nonempty_string(evidence.get("servedOrigin"), "servedOrigin")
    parsed = urlparse(origin)
    require(parsed.scheme == "https", "servedOrigin must use HTTPS")
    require(bool(parsed.hostname), "servedOrigin must contain a hostname")
    require(parsed.username is None and parsed.password is None, "servedOrigin must not contain credentials")
    require(parsed.query == "" and parsed.fragment == "", "servedOrigin must not contain query or fragment")

    artifacts = evidence.get("artifacts")
    require(isinstance(artifacts, dict), "artifacts must be an object")
    js_path = require_nonempty_string(artifacts.get("javascriptPath"), "artifacts.javascriptPath")
    wasm_path = require_nonempty_string(artifacts.get("wasmPath"), "artifacts.wasmPath")
    require(js_path.endswith(".js"), "artifacts.javascriptPath must identify generated JavaScript glue")
    require(wasm_path.endswith(".wasm"), "artifacts.wasmPath must identify a WebAssembly module")
    require_sha256(artifacts.get("javascriptSha256"), "artifacts.javascriptSha256")
    require_sha256(artifacts.get("wasmSha256"), "artifacts.wasmSha256")

    execution = evidence.get("execution")
    require(isinstance(execution, dict), "execution must be an object")
    for field in (
        "realBrowserExecuted",
        "generatedBindingsLoaded",
        "wasmInitialized",
        "bitwardenVectorPassed",
        "authenticationMaterialMatched",
        "sameOriginLoadObserved",
        "providerRegistrationWasExplicit",
    ):
        require(execution.get(field) is True, f"execution.{field} must be true")

    csp = evidence.get("csp")
    require(isinstance(csp, dict), "csp must be an object")
    require_nonempty_string(csp.get("effectivePolicy"), "csp.effectivePolicy")
    violations = csp.get("violations")
    require(isinstance(violations, list), "csp.violations must be an array")
    require(len(violations) == 0, "csp.violations must be empty")

    performance = evidence.get("performance")
    require(isinstance(performance, dict), "performance must be an object")
    samples = performance.get("samples")
    require(isinstance(samples, int) and not isinstance(samples, bool) and samples >= 3, "performance.samples must be an integer >= 3")
    p50 = validate_positive_number(performance.get("deriveMsP50"), "performance.deriveMsP50")
    p95 = validate_positive_number(performance.get("deriveMsP95"), "performance.deriveMsP95")
    maximum = validate_positive_number(performance.get("deriveMsMax"), "performance.deriveMsMax")
    require(p50 <= p95 <= maximum, "performance timings must satisfy p50 <= p95 <= max")

    memory = evidence.get("memory")
    require(isinstance(memory, dict), "memory must be an object")
    require_nonempty_string(memory.get("method"), "memory.method")
    before = validate_positive_number(memory.get("beforeBytes"), "memory.beforeBytes", allow_zero=True)
    after = validate_positive_number(memory.get("afterBytes"), "memory.afterBytes", allow_zero=True)
    peak = validate_positive_number(memory.get("peakBytes"), "memory.peakBytes", allow_zero=True)
    require(peak >= before and peak >= after, "memory.peakBytes must be >= beforeBytes and afterBytes")
    require(memory.get("leakSuspected") is False, "memory.leakSuspected must be false")

    approvals = evidence.get("approvals")
    require(isinstance(approvals, dict), "approvals must be an object")
    require(approvals.get("credentialProcessingApproved") is False, "credentialProcessingApproved must remain false")
    require(approvals.get("productionReleaseApproved") is False, "productionReleaseApproved must remain false")
    require(approvals.get("stablePromotionApproved") is False, "stablePromotionApproved must remain false")

    require(evidence.get("accepted") is True, "accepted must be true only for a completed passing real-browser run")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
        validate_evidence(data)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(f"browser Argon2id evidence invalid: {exc}", file=sys.stderr)
        return 1

    print("browser Argon2id evidence valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
