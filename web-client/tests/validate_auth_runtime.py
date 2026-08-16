#!/usr/bin/env python3
"""Fail-closed structural validation for GoreeVault Web authentication/runtime modules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULES = {
    "assets/argon2id-provider.js": [
        "builtInImplementationAvailable: false",
        "fallbackAllowed: false",
        "credentialProcessingEnabledByRegistration: false",
        "Argon2id authentication remains unavailable",
        "secretBytes.fill(0)",
        "saltBytes.fill(0)",
        "exactly ${MASTER_KEY_BYTES} bytes",
        "independent buffer",
    ],
    "assets/auth-kdf.js": [
        "PBKDF2_MIN_ITERATIONS = 5000",
        "hash: 'SHA-256'",
        "SERVER_AUTHORIZATION_PURPOSE = 1",
        "requireArgon2idProvider",
        "masterKey.fill(0)",
    ],
    "assets/identity-protocol.js": [
        "/identity/connect/token",
        "application/x-www-form-urlencoded",
        "Identity token exchange is disabled",
        "credentials: 'same-origin'",
        "cache: 'no-store'",
        "redirect: 'error'",
    ],
    "assets/token-state.js": [
        "storage: 'memory-only'",
        "Stale refresh response rejected",
        "Refresh-token replay rejected",
        "Refresh token did not rotate; session invalidated",
    ],
    "assets/authenticated-api.js": [
        "Authorization",
        "No usable access token exists for the selected account",
        "authentication_required",
        "clearTokenState",
    ],
    "assets/sync-client.js": [
        "/api/sync",
        "Vault scope does not match the selected account",
        "normalizeSyncEnvelope",
        "acceptOpaqueSync",
    ],
}

TESTS = [
    "tests/auth-kdf.test.js",
    "tests/identity-protocol.test.js",
    "tests/token-state.test.js",
    "tests/authenticated-api.test.js",
    "tests/sync-client.test.js",
]

FORBIDDEN = [
    "localStorage.setItem('token",
    'localStorage.setItem("token',
    "sessionStorage.setItem('token",
    'sessionStorage.setItem("token',
    "console.log(",
    "console.debug(",
]


def main() -> int:
    try:
        combined = []
        for relative, tokens in MODULES.items():
            path = ROOT / relative
            if not path.is_file():
                raise ValueError(f"missing authentication runtime module: {relative}")
            source = path.read_text(encoding="utf-8")
            combined.append(source)
            missing = [token for token in tokens if token not in source]
            if missing:
                raise ValueError(f"{relative} is missing required security tokens: {missing}")

        tests = []
        for relative in TESTS:
            path = ROOT / relative
            if not path.is_file():
                raise ValueError(f"missing authentication runtime test: {relative}")
            tests.append(path.read_text(encoding="utf-8"))

        test_source = "\n".join(tests)
        for required in [
            "Bitwarden SDK vector",
            "Argon2id remains fail-closed",
            "without PBKDF2 fallback",
            "network token exchange stays fail-closed",
            "non-rotating refresh token invalidates the session",
            "401 invalidates the memory-only token session",
            "stale in-flight sync response",
        ]:
            if required not in test_source:
                raise ValueError(f"missing authentication runtime regression coverage: {required}")

        runtime_source = "\n".join(combined)
        lowered = runtime_source.lower()
        found = [token for token in FORBIDDEN if token.lower() in lowered]
        if found:
            raise ValueError(f"forbidden token/debug persistence surface found: {found}")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"GoreeVault Web authentication runtime validation failed: {exc}", file=sys.stderr)
        return 1

    print("GoreeVault Web KDF, Argon2id provider, identity, token rotation, authenticated transport, and sync runtime validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
