# GoreeVault Web — Incubation Workspace

## Status

**Pre-Alpha — not approved for production use.**

This directory is the temporary GoreeVault Web incubation workspace. It exists only because the current GitHub integration cannot create the planned standalone `GoreeCloud/goreevault-web` repository.

Before Stable, this application must move to its own GoreeCloud-owned repository and release lifecycle as required by `docs/WEB-CLIENT-CONTRACT.md`.

## Role and Purpose

**Role:** Primary GoreeCloud-owned browser client for GoreeVault.

**Purpose:** Provide a secure, privacy-first, multi-user browser experience for storing and using encrypted credentials while preserving the GoreeVault Server zero-knowledge boundary and approved compatible protocol behavior.

## Current implementation slice

This first slice deliberately implements only the browser application shell and presentation/security foundation:

- GoreeVault identity;
- Glaze UI tokens, layered surfaces, responsive layout, and local presentation assets;
- System, Light, and Dark appearance modes;
- visible keyboard focus and skip navigation;
- reduced-motion, increased-contrast, forced-colors, and reduced-transparency behavior;
- local-only JavaScript, CSS, and SVG assets;
- restrictive browser policy metadata;
- no analytics, telemetry, advertising, remote fonts, remote icon libraries, or third-party browser scripts;
- explicit locked/pre-alpha state with no fake credential handling or invented cryptography.

This slice **does not** implement vault decryption, key derivation, authentication, sync, WebAuthn, attachments, organizations, TOTP, import/export, or persistent credential storage. Those features must be added only against the GoreeVault Web contract and compatible server protocol.

## Security boundary

The shell must not store or process real credentials yet. UI development must never introduce placeholder cryptography, fake encryption, plaintext vault persistence, or console logging of secrets simply to make screens appear functional.

See `docs/SECURITY-BOUNDARY.md`.

## Validation

Run:

```sh
python3 web-client/tests/validate_web_shell.py
node --check web-client/assets/theme-init.js
node --check web-client/assets/app.js
```

The validation gate checks local-only browser dependencies, required privacy/security metadata, Glaze UI/accessibility behavior, and the explicit pre-alpha safety boundary.

## Stable boundary

Creating this shell does not close the GoreeVault product-wide Glaze UI blocker. Stable still requires the complete supported browser workflow matrix, client-side zero-knowledge implementation, real accessibility acceptance, immutable browser build identity, migration/rollback proof, real-client testing, WebAuthn/passkey evidence, target-environment rehearsal, governance, and final exact-RC evidence.
