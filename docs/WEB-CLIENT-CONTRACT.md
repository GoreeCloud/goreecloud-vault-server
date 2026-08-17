# GoreeVault Web Client Contract

## Purpose

This document defines the implementation boundary for **GoreeVault Web**, the planned GoreeCloud-owned browser vault client.

GoreeVault Web is required on the current path to product-wide Stable readiness because the existing bundled upstream-compatible web vault is a temporary compatibility dependency and does not satisfy GoreeCloud's product-wide Glaze UI ownership requirement.

This contract does not authorize a browser-vault cutover and does not claim that a separate GoreeVault Web repository already exists. The planned client remains a distinct application/repository boundary because it will own client-side cryptography, browser storage, dependencies, build artifacts, accessibility behavior, Glaze UI, and its own release lifecycle.

## Role and Purpose

**Role:** Primary GoreeCloud-owned browser client for GoreeVault.

**Purpose:** Provide a secure, privacy-first, multi-user browser experience for storing and using encrypted credentials while preserving the GoreeVault Server zero-knowledge boundary and approved Bitwarden-compatible protocol behavior.

GoreeVault Web must never become a server-side decryption layer, a credential-inspection service, or a branding wrapper around the upstream web vault.

## Architectural boundary

GoreeVault Web owns:

- browser presentation and interaction;
- Glaze UI application shell and component behavior;
- client-side vault encryption/decryption;
- client-side key lifecycle and lock state;
- browser-local encrypted state;
- browser authentication/session handling;
- GoreeVault Server API integration;
- accessibility and responsive behavior;
- client-side import/export UX;
- browser release, dependency, and supply-chain controls.

GoreeVault Server owns:

- authenticated API behavior;
- user/account persistence;
- authorization enforcement;
- organization and collection authorization;
- encrypted vault object persistence;
- attachment persistence and authorization;
- token issuance/rotation/revocation;
- server-side WebAuthn/passkey protocol participation;
- rate limiting, security headers, and backend policy;
- database migrations and recovery.

Neither boundary authorizes the server to receive or retain plaintext master passwords, decrypted vault contents, derived encryption keys, decrypted attachments, TOTP seeds, or other client-side plaintext secrets that are not required by the established compatible protocol.

## Canonical server origin

Production GoreeVault Web uses:

`https://vault.goreecloud.com`

The client must not require a third-party hosted control plane, telemetry endpoint, analytics service, CDN, remote font service, or proprietary API for ordinary vault operation.

Development environments may use explicitly configured local/test origins. Development defaults must never silently become production defaults.

## Cryptography and zero-knowledge requirements

GoreeVault Web must preserve the current GoreeVault security policy:

1. Do not invent cryptographic primitives.
2. Do not redesign password hashing, KDF behavior, symmetric/asymmetric encryption, WebAuthn/passkey behavior, token signing, or key derivation merely for GoreeCloud ownership or visual identity.
3. Use mature, reviewed, interoperable primitives and protocol behavior compatible with the supported GoreeVault Server baseline.
4. Treat decrypted vault contents and derived keys as short-lived client memory, not general application state.
5. Persist only encrypted vault material or protocol-required non-secret metadata in browser storage.
6. Clear decrypted state and key material on lock, logout, account switch, and session invalidation.
7. Never place secrets in URLs, analytics events, client logs, crash reports, DOM attributes intended for telemetry/debugging, or browser console output.
8. Never send decrypted vault contents to a GoreeCloud service other than where an explicitly supported end-to-end encrypted protocol requires client-produced ciphertext.

Any cryptographic or protocol departure requires a separate threat model, migration plan, rollback plan, interoperability review, and dedicated security approval.

## Multi-user requirements

GoreeVault Web is a multi-user application. It must support individual GoreeVault identities and must not assume a single shared household or administrator account.

The browser client must:

- keep account/session state explicitly scoped to the selected identity;
- prevent one signed-in user from reading another user's cached encrypted or decrypted application state through ordinary UI flows;
- clear sensitive in-memory state on account switch;
- honor server-side authorization and membership changes after refresh/sync;
- honor session/device invalidation;
- make organization and collection context clear without weakening server authorization;
- avoid shared administrator credentials as the normal family-user model;
- keep NetBird/private-network connectivity separate from application identity and authorization.

## Required compatibility surface before cutover

Before GoreeVault Web may replace the bundled upstream web vault as the primary production browser client, exact-candidate testing must cover at minimum:

- prelogin and sign-in;
- unlock and lock;
- refresh-token rotation and replay rejection behavior;
- full vault sync;
- personal cipher create/read/update/delete;
- secure notes and supported item types;
- attachments;
- organizations, memberships, collections, and permission changes;
- TOTP workflows;
- WebAuthn/passkey registration and authentication;
- logout and device/session invalidation;
- import/export behavior selected for the supported release;
- error, offline/interruption, and reauthentication behavior relevant to data safety.

Feature parity must be defined by an explicit supported-release checklist. GoreeVault Web must not silently replace a working upstream-compatible browser client while required supported workflows are missing.

## Browser storage and session policy

Browser-local storage is part of the security boundary.

Required rules:

- no plaintext vault items in `localStorage`, `sessionStorage`, IndexedDB, Cache Storage, service-worker caches, or persistent filesystem APIs;
- no master password persistence;
- no derived encryption-key persistence unless an explicitly reviewed secure-unlock design requires protected platform storage;
- tokens are scoped and retained only as required by the approved compatible session model;
- lock and logout clear decrypted in-memory state;
- account removal clears account-scoped browser state;
- service workers, if introduced, must not cache authenticated API responses containing private vault data unless the stored representation is encrypted and explicitly reviewed;
- browser debugging must not expose reusable credentials or decrypted values.

An offline-capable design is permitted only after its encrypted-storage, key-lifecycle, update, and recovery behavior is explicitly reviewed.

## Glaze UI requirements

GoreeVault Web uses **Glaze UI Design Language** as its complete presentation and interaction system, not as a superficial theme layer.

Required product behavior includes:

- GoreeVault product identity throughout the controlled browser experience;
- layered Glaze surfaces with restrained translucency and clear hierarchy;
- consistent navigation, form, dialog, list, menu, notification, and empty/error states;
- System, Light, and Dark appearance modes;
- responsive desktop/tablet/mobile browser layouts;
- visible keyboard focus;
- complete keyboard operability for core vault workflows;
- reduced-motion support;
- increased-contrast support;
- forced-colors/High Contrast operability;
- meaningful accessible names, labels, status announcements, and error relationships;
- touch targets and spacing appropriate to mobile browsers;
- no remote presentation dependencies required for ordinary operation;
- no analytics, behavioral tracking, advertising SDKs, or fingerprinting.

Security-sensitive controls such as reveal, copy, autofill, delete, export, account removal, and session revocation must prioritize clarity over decorative effects.

## Content Security Policy and dependency boundary

The production browser client should be buildable and operable with local application assets.

Its deployment design must support a restrictive Content Security Policy that avoids unnecessary remote origins and avoids `unsafe-eval`. Any requirement for `unsafe-inline`, third-party script origins, remote fonts, remote stylesheets, or broadly permissive `connect-src` values is a security exception requiring review and removal planning.

Dependencies must be:

- open source under GoreeCloud-approved licensing;
- locked reproducibly;
- reviewed for necessity;
- scanned for known vulnerabilities;
- attributable through an SBOM or equivalent release artifact;
- replaceable or removable without losing access to GoreeVault data.

## Privacy and telemetry

GoreeVault Web does not use analytics or behavioral telemetry in its default production build.

Operational diagnostics must minimize personal data and must never include:

- master passwords;
- decrypted vault fields;
- TOTP seeds;
- recovery codes;
- private keys;
- session cookies;
- bearer/refresh tokens;
- decrypted attachments;
- full database credentials;
- unredacted authorization headers.

If crash diagnostics are added later, they require explicit privacy review, local/self-hosted preference evaluation, redaction verification, and opt-in/disable behavior appropriate to GoreeCloud policy.

## Accessibility acceptance

Before production cutover, GoreeVault Web requires browser acceptance evidence covering at minimum:

- keyboard-only sign-in, unlock, search, item navigation, editing, save/cancel, copy/reveal, dialogs, and logout;
- visible focus order;
- screen-reader labels and error announcements for core workflows;
- zoom/reflow behavior;
- reduced motion;
- Light/Dark/System modes;
- increased contrast;
- forced colors/High Contrast;
- narrow mobile-browser layouts;
- no inaccessible interaction that is available only through hover, color, animation, or pointer precision.

Automated accessibility testing supplements but does not replace real browser acceptance.

## Release and supply-chain requirements

A GoreeVault Web Release Candidate must provide:

- exact source commit identity;
- reproducible locked dependencies;
- automated unit/integration/browser tests;
- dependency/security scanning;
- Glaze UI and accessibility source gates;
- server compatibility tests against the exact GoreeVault Server candidate;
- immutable browser asset/build identity;
- SBOM or equivalent dependency inventory;
- documented rollback to the previously accepted browser client;
- release evidence tied to the exact candidate.

A mutable branch build or unversioned asset cannot satisfy Stable evidence.

## Migration and fallback

The upstream-compatible web vault remains available as a compatibility/fallback asset until GoreeVault Web has passed its approved compatibility, security, accessibility, migration, and recovery gates.

Cutover must be reversible. The production change must record:

- previous browser client/version;
- new GoreeVault Web source and artifact identity;
- GoreeVault Server artifact identity;
- compatibility evidence;
- browser/accessibility evidence;
- rollback procedure;
- operator and timestamp;
- outcome.

Rollback must not require database downgrade or plaintext export merely to restore the previously working browser presentation.

## Stable-release gate

GoreeVault Web closes the current product-wide Glaze UI blocker only when all of the following are true:

1. the primary production browser vault is GoreeCloud-owned;
2. Glaze UI conformance is proven across the controlled browser experience;
3. zero-knowledge and client-side cryptographic boundaries are preserved;
4. the supported browser workflow matrix passes against the exact GoreeVault Server candidate;
5. accessibility acceptance passes;
6. release/build artifacts are immutable and traceable;
7. migration and rollback are proven;
8. the exact-RC Stable evidence record identifies the accepted browser asset and marks the Glaze UI section complete.

Starting GoreeVault Web development, creating a repository, or rendering a Glaze UI shell does not close the blocker by itself.
