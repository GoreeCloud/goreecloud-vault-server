# GoreeVault Web Security Boundary

## Current state

GoreeVault Web is pre-alpha. The current implementation is an application shell only and must not be used with real vault credentials.

## Non-negotiable rules

- Do not invent cryptographic primitives.
- Do not persist master passwords, plaintext vault items, derived keys, decrypted attachments, TOTP seeds, recovery codes, bearer tokens, or refresh tokens in general browser storage.
- Do not log secrets to the browser console, DOM diagnostics, telemetry, crash reports, URLs, or analytics events.
- Do not add analytics, advertising, fingerprinting, remote fonts, third-party browser scripts, or a hosted control plane for ordinary operation.
- Treat NetBird/private-network reachability as transport access only; it is not application authorization.
- Keep all account/session state explicitly scoped to the selected GoreeVault identity.
- Clear decrypted state and key material on lock, logout, account switch, account removal, and session invalidation.
- Service workers must not cache authenticated private API responses unless the representation is encrypted and separately reviewed.

## Implementation sequencing

The application shell may be developed before protocol integration. Authentication, key derivation, vault encryption/decryption, persistent encrypted storage, WebAuthn/passkey flows, sync, attachments, organizations, TOTP, import/export, and offline behavior must each be implemented against the documented GoreeVault Server compatibility baseline and reviewed security model.

UI prototypes must remain obviously non-functional where secure protocol behavior is not implemented. A visual mock must never masquerade as working credential security.

## Content Security Policy direction

The production client must remain compatible with a restrictive CSP using local application assets and avoiding `unsafe-eval`. Any future requirement for `unsafe-inline`, third-party script/style origins, remote fonts, or broad `connect-src` entries requires explicit security review and a removal plan.

## Production boundary

This incubation directory must move to the dedicated GoreeVault Web repository before Stable so browser dependencies, releases, SBOMs, immutable artifacts, compatibility evidence, and rollback records have their own lifecycle and review boundary.
