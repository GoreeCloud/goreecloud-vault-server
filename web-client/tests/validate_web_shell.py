#!/usr/bin/env python3
"""Fail-closed source validation for the GoreeVault Web incubation client."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def validate_html() -> None:
    html = read("index.html")
    required = [
        'data-glaze-ui',
        'name="robots" content="noindex,nofollow,noarchive"',
        'name="referrer" content="same-origin"',
        'http-equiv="Content-Security-Policy"',
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        'href="#main">Skip to vault workspace</a>',
        'id="main" tabindex="-1"',
        'id="appearance-toggle"',
        'aria-live="polite"',
        'Local shell only · no credential processing',
    ]
    missing = [token for token in required if token not in html]
    require(not missing, f"index.html is missing required shell contract tokens: {missing}")

    for remote in re.findall(r'(?:src|href)="(https?://[^"]+)"', html):
        raise ValueError(f"remote presentation dependency is not allowed: {remote}")

    csp_match = re.search(r'Content-Security-Policy" content="([^"]+)"', html)
    require(csp_match is not None, "CSP metadata is required")
    csp = csp_match.group(1)
    require("unsafe-eval" not in csp, "CSP must not allow unsafe-eval")
    require("unsafe-inline" not in csp, "CSP must not allow unsafe-inline")
    require("https://vault.goreecloud.com" in csp, "canonical GoreeVault Server origin must be explicit")
    require('type="password"' not in html.lower(), "password entry must remain absent while credential processing is disabled")


def validate_css() -> None:
    css = read("assets/glaze.css")
    required = [
        "backdrop-filter",
        "border-radius",
        "prefers-reduced-motion: reduce",
        "prefers-contrast: more",
        "forced-colors: active",
        "prefers-reduced-transparency: reduce",
        ":focus-visible",
        "min-height: 44px",
        'data-appearance="light"',
        'data-appearance="dark"',
    ]
    missing = [token for token in required if token not in css]
    require(not missing, f"Glaze UI stylesheet is missing accessibility/design tokens: {missing}")
    require("@import url(" not in css.lower(), "remote CSS imports are not allowed")


def validate_javascript() -> None:
    files = [
        "assets/theme-init.js",
        "assets/app.js",
        "assets/runtime-config.js",
        "assets/session-state.js",
        "assets/crypto-boundary.js",
        "assets/api-errors.js",
        "assets/api-client.js",
        "assets/auth-protocol.js",
        "assets/auth-state.js",
        "assets/auth-request.js",
        "assets/auth-kdf.js",
        "assets/server-config.js",
        "assets/sync-protocol.js",
        "assets/vault-state.js",
    ]
    combined = "\n".join(read(path) for path in files)
    require("goreevault-web-appearance" in combined, "appearance preference key is required")
    require("system" in combined and "light" in combined and "dark" in combined, "System/Light/Dark modes are required")
    require("https://vault.goreecloud.com" in combined, "canonical production API origin is required")
    require("credentialProcessingEnabled: false" in combined, "credential processing must remain fail-closed")
    require("persistentDecryptedStateEnabled: false" in combined, "decrypted persistence must remain disabled")
    require("offlinePrivateResponseCachingEnabled: false" in combined, "private response caching must remain disabled")
    require("unavailable-pre-alpha" in combined, "vault cryptography adapter must remain explicitly unavailable")
    require("clearSession" in combined and "switchAccount" in combined, "account/session clearing boundary is required")
    require("sessionEpoch" in combined, "session invalidation epoch is required")

    require("/api/accounts/prelogin" in combined, "compatible prelogin endpoint boundary is required")
    require("kdfIterations" in combined and "kdfMemory" in combined and "kdfParallelism" in combined,
            "prelogin KDF metadata must be modeled explicitly")
    require("PBKDF2_MIN_ITERATIONS = 5000" in combined, "Bitwarden PBKDF2 minimum must be enforced")
    require("hash: 'SHA-256'" in combined, "PBKDF2-SHA256 authentication KDF is required")
    require("SERVER_AUTHORIZATION_PURPOSE = 1" in combined, "server authorization hash purpose must remain explicit")
    require("Argon2id authentication remains unavailable" in combined,
            "Argon2id must stay fail-closed until a reviewed local implementation exists")
    require("masterKey.fill(0)" in combined, "temporary PBKDF2 master key material must be cleared after hash derivation")
    require("TwoFactorProviders" in combined and "Two factor required." in combined,
            "compatible two-factor challenge shape must be modeled explicitly")
    require("PASSWORD_SCOPE = 'api offline_access'" in combined, "password grant scope must match the compatible server")
    require("WEB_CLIENT_ID = 'web'" in combined, "browser client identity must remain explicit")
    require("UNKNOWN_BROWSER_DEVICE_TYPE = 14" in combined, "default browser device type must remain explicit")
    require("buildPasswordGrantEnvelope" in combined, "non-secret password grant envelope is required")
    require("Secret-bearing password grants are disabled" in combined,
            "secret-bearing password grants must remain fail-closed")
    require("persistentTokenStorageEnabled: false" in combined, "persistent token storage must remain disabled")
    require("refreshRotationRequired: true" in combined, "refresh-token rotation requirement must remain explicit")
    require("replayRejectionRequired: true" in combined, "refresh-token replay rejection requirement must remain explicit")
    require("/api/config" in combined, "server configuration verification endpoint is required")
    require("/api/sync" in combined, "compatible sync endpoint boundary is required")
    require("credentials: 'same-origin'" in combined, "API requests must not broaden credential scope")
    require("cache: 'no-store'" in combined, "API requests must not use general browser caching")
    require("redirect: 'error'" in combined, "API requests must reject redirects")
    require("AbortController" in combined, "abortable API request handling is required")
    require("requestEpoch" in combined and "Stale prelogin response rejected" in combined,
            "authentication requests must reject stale account-scoped responses")
    require("GoreeVaultApiError" in combined, "normalized API error type is required")

    forbidden = [
        "console.log(",
        "console.debug(",
        "fetch('http",
        'fetch("http',
        "google-analytics",
        "gtag(",
        "segment.com",
        "mixpanel",
        "localstorage.setitem('token",
        'localstorage.setitem("token',
        "localstorage.setitem('password",
        'localstorage.setitem("password',
        "sessionstorage.setitem('token",
        'sessionstorage.setitem("token',
        "sessionstorage.setitem('password",
        'sessionstorage.setitem("password',
    ]
    lowered = combined.lower()
    found = [token for token in forbidden if token in lowered]
    require(not found, f"forbidden browser telemetry/debug/secret persistence surface found: {found}")


def validate_test_harness() -> None:
    package = read("package.json")
    require('"private": true' in package, "incubation package must remain private")
    require('"type": "module"' in package, "ES module test boundary is required")
    require('node --test tests/*.test.js' in package, "Node unit-test command is required")

    tests = "\n".join([
        read("tests/api-client.test.js"),
        read("tests/auth-protocol.test.js"),
        read("tests/auth-state.test.js"),
        read("tests/auth-kdf.test.js"),
        read("tests/prelogin-ui.test.js"),
        read("tests/server-config.test.js"),
        read("tests/sync-boundary.test.js"),
    ])
    for token in [
        "same-origin credential scope",
        "stale failures cannot overwrite",
        "secret-bearing grants and token lifecycle stay fail-closed",
        "two-factor challenges",
        "PBKDF2 master-key derivation matches the Bitwarden SDK vector",
        "Argon2id remains fail-closed",
        "cross-account",
    ]:
        require(token in tests, f"missing protocol/security regression coverage: {token}")


def validate_release_builder() -> None:
    builder = read("scripts/build_release.py")
    builder_tests = read("tests/test_build_release.py")
    require("RELEASE_FILES" in builder, "release builder must use an explicit file allowlist")
    require("sha256" in builder and "sourceRevision" in builder, "release manifest identity is required")
    require('"runtimeDependencies": []' in builder, "runtime dependency inventory must remain explicit")
    require("deterministic" in builder_tests.lower(), "deterministic release behavior must be tested")


def validate_security_docs() -> None:
    readme = read("README.md")
    security = read("docs/SECURITY-BOUNDARY.md")
    require("not approved for production use" in readme, "README must preserve pre-production state")
    require("must move to its own GoreeCloud-owned repository" in readme, "standalone repository requirement must remain explicit")
    require("Do not invent cryptographic primitives" in security, "security boundary must prohibit invented cryptography")
    require("must not be used with real vault credentials" in security, "pre-alpha real-credential prohibition is required")
    require("plaintext vault" in security, "plaintext storage prohibition must be documented")
    require("account/session state explicitly scoped" in security, "account-scoped session requirement must be documented")
    require("Clear decrypted state and key material" in security, "sensitive-state clearing requirement must be documented")
    require("Prelogin" in security and "KDF metadata" in security, "prelogin protocol scope must be documented")
    require("password entry remains disabled" in security, "password-processing prohibition must remain explicit")
    require("opaque sync" in security.lower(), "opaque sync limitation must remain documented")


def validate_svg() -> None:
    svg = read("assets/goreevault-mark.svg")
    require("<script" not in svg.lower(), "identity SVG must be script-free")
    require("http://www.w3.org/2000/svg" in svg, "identity asset must be a local SVG")


def main() -> int:
    required_files = [
        "README.md",
        "package.json",
        "index.html",
        "assets/glaze.css",
        "assets/theme-init.js",
        "assets/app.js",
        "assets/runtime-config.js",
        "assets/session-state.js",
        "assets/crypto-boundary.js",
        "assets/api-errors.js",
        "assets/api-client.js",
        "assets/auth-protocol.js",
        "assets/auth-state.js",
        "assets/auth-request.js",
        "assets/auth-kdf.js",
        "assets/server-config.js",
        "assets/sync-protocol.js",
        "assets/vault-state.js",
        "assets/goreevault-mark.svg",
        "docs/SECURITY-BOUNDARY.md",
        "scripts/build_release.py",
        "tests/test_build_release.py",
        "tests/api-client.test.js",
        "tests/auth-protocol.test.js",
        "tests/auth-state.test.js",
        "tests/auth-kdf.test.js",
        "tests/prelogin-ui.test.js",
        "tests/server-config.test.js",
        "tests/sync-boundary.test.js",
    ]
    try:
        for path in required_files:
            require((ROOT / path).is_file(), f"missing required GoreeVault Web file: {path}")
        validate_html()
        validate_css()
        validate_javascript()
        validate_test_harness()
        validate_release_builder()
        validate_security_docs()
        validate_svg()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"GoreeVault Web validation failed: {exc}", file=sys.stderr)
        return 1

    print("GoreeVault Web Glaze UI, protocol, KDF, release, privacy, and client-safety validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
