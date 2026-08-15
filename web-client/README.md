# GoreeVault Web — Incubation Workspace

## Status

**Pre-Alpha — not approved for production use.**

This directory is the temporary GoreeVault Web incubation workspace. It exists only because the current GitHub integration cannot create the planned standalone `GoreeCloud/goreevault-web` repository.

Before Stable, this application must move to its own GoreeCloud-owned repository and release lifecycle as required by `docs/WEB-CLIENT-CONTRACT.md`.

## Role and Purpose

**Role:** Primary GoreeCloud-owned browser client for GoreeVault.

**Purpose:** Provide a secure, privacy-first, multi-user browser experience for storing and using encrypted credentials while preserving the GoreeVault Server zero-knowledge boundary and approved compatible protocol behavior.

## Current implementation slices

The first slice establishes the browser application shell and presentation/security foundation:

- GoreeVault identity;
- Glaze UI tokens, layered surfaces, responsive layout, and local presentation assets;
- System, Light, and Dark appearance modes;
- visible keyboard focus and skip navigation;
- reduced-motion, increased-contrast, forced-colors, and reduced-transparency behavior;
- local-only JavaScript, CSS, and SVG assets;
- restrictive browser policy metadata;
- no analytics, telemetry, advertising, remote fonts, remote icon libraries, or third-party browser scripts;
- explicit locked/pre-alpha state with no fake credential handling or invented cryptography.

The second slice establishes fail-closed client architecture boundaries without enabling credential use:

- canonical production server origin resolution to `https://vault.goreecloud.com`;
- explicit development-origin allowlisting rather than implicit production fallback changes;
- account-scoped, memory-only session state with explicit lock, logout, account-switch, and invalidation transitions;
- session epochs for invalidating stale account-scoped state;
- disabled credential-processing, decrypted-persistence, and private-response-cache feature flags;
- an explicit cryptography adapter boundary that throws until a reviewed compatible implementation exists;
- CI/source validation that fails if these pre-alpha controls are weakened accidentally.

The third slice establishes the protocol-facing authentication foundation while keeping real credential processing disabled:

- abortable, timeout-bounded GoreeVault API requests using `cache: no-store`, same-origin credential scope, and redirect rejection;
- normalized API errors that expose status/category information without logging request bodies, tokens, passwords, or server responses to the console;
- the existing compatible `/api/accounts/prelogin` endpoint for account-identifier preflight only;
- explicit validation of `kdf`, `kdfIterations`, `kdfMemory`, and `kdfParallelism` metadata returned by GoreeVault Server;
- account-scoped authentication phases and request epochs that reject stale prelogin responses after account changes;
- an explicit token lifecycle contract requiring refresh-token rotation and replay rejection while persistent token storage remains disabled;
- token acceptance, refresh exchange, revocation, password processing, KDF execution, sign-in submission, and vault unlock remain intentionally unavailable.

These slices **do not** implement vault decryption, key derivation, real sign-in, token persistence, authenticated sync, WebAuthn, attachments, organizations, TOTP, import/export, or persistent credential storage. Those features must be added only against the GoreeVault Web contract and compatible server protocol.

## Security boundary

The shell must not store or process real credentials yet. UI development must never introduce placeholder cryptography, fake encryption, plaintext vault persistence, or console logging of secrets simply to make screens appear functional.

Appearance is the only current browser-local preference. Account/session/authentication state remains in memory, and no reusable credentials or decrypted vault material are written to general browser storage. Prelogin handles only the normalized account identifier and server-provided KDF metadata; password entry and all secret-bearing authentication operations remain disabled.

See `docs/SECURITY-BOUNDARY.md`.

## Validation

Run:

```sh
python3 web-client/tests/validate_web_shell.py
node --check web-client/assets/theme-init.js
node --check web-client/assets/app.js
node --check web-client/assets/runtime-config.js
node --check web-client/assets/session-state.js
node --check web-client/assets/crypto-boundary.js
node --check web-client/assets/api-errors.js
node --check web-client/assets/api-client.js
node --check web-client/assets/auth-protocol.js
node --check web-client/assets/auth-state.js
```

The validation gate checks local-only browser dependencies, required privacy/security metadata, Glaze UI/accessibility behavior, canonical runtime configuration, account/session isolation, disabled secret persistence, the unavailable cryptography boundary, bounded API behavior, compatible prelogin metadata handling, stale-response rejection, disabled token persistence, and the explicit pre-alpha safety state.

## Stable boundary

Creating these foundations does not close the GoreeVault product-wide Glaze UI blocker. Stable still requires the complete supported browser workflow matrix, client-side zero-knowledge implementation, real accessibility acceptance, immutable browser build identity, migration/rollback proof, real-client testing, WebAuthn/passkey evidence, target-environment rehearsal, governance, and final exact-RC evidence.
