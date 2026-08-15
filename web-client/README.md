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

These slices **do not** implement vault decryption, key derivation, authentication, sync, WebAuthn, attachments, organizations, TOTP, import/export, or persistent credential storage. Those features must be added only against the GoreeVault Web contract and compatible server protocol.

## Security boundary

The shell must not store or process real credentials yet. UI development must never introduce placeholder cryptography, fake encryption, plaintext vault persistence, or console logging of secrets simply to make screens appear functional.

Appearance is the only current browser-local preference. Account/session state remains in memory, and no reusable credentials or decrypted vault material are written to general browser storage.

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
```

The validation gate checks local-only browser dependencies, required privacy/security metadata, Glaze UI/accessibility behavior, canonical runtime configuration, account/session isolation, disabled secret persistence, the unavailable cryptography boundary, and the explicit pre-alpha safety state.

## Stable boundary

Creating these foundations does not close the GoreeVault product-wide Glaze UI blocker. Stable still requires the complete supported browser workflow matrix, client-side zero-knowledge implementation, real accessibility acceptance, immutable browser build identity, migration/rollback proof, real-client testing, WebAuthn/passkey evidence, target-environment rehearsal, governance, and final exact-RC evidence.
