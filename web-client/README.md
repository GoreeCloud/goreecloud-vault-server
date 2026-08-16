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
- compatible non-secret password-grant envelope modeling with `client_id=web`, `scope=api offline_access`, and explicit browser-device metadata;
- compatible two-factor challenge modeling without accepting or transmitting a two-factor secret;
- account-scoped authentication phases and request epochs that reject stale prelogin responses after account changes;
- vector-tested PBKDF2-SHA256 master-key derivation and server-authorization hashing for the reviewed PBKDF2 compatibility path;
- memory-only token lifecycle modeling with expiry checks, refresh generations, stale-response rejection, refresh-token rotation, and replay rejection;
- real password-grant transmission, production token exchange/refresh, and two-factor completion remain intentionally unavailable while credential processing is disabled.

The fourth slice adds a functional Glaze UI prelogin-only experience and server capability verification:

- an email-only account-preparation form with accessible progress and result announcements;
- no password field and no secret-bearing authentication submission;
- `/api/config` verification requiring GoreeVault server identity and the approved production origin before prelogin proceeds;
- explicit display of the verified server version and KDF family after successful account preparation;
- automated source tests that fail if a password input or secret-bearing sign-in path appears while credential processing remains disabled.

The fifth slice establishes sync and release-engineering boundaries without enabling private-data use:

- structural validation of the compatible `/api/sync` envelope containing profile, folders, collections, policies, ciphers, domains, sends, and user-decryption metadata;
- account-scoped authenticated sync composition from an already accepted in-memory token through `/api/sync` into opaque memory-only vault state;
- stale-epoch and cross-account sync rejection;
- vector-tested master-key stretching, AES-256-CBC-HMAC-SHA256 integrity/decryption, type-2 `EncString` parsing, composite user-key unwrap, and scoped user-key clearing;
- the public end-to-end vault cryptography adapter remains unavailable, and persistent encrypted cache plus decrypted vault presentation remain disabled;
- a zero-dependency Node test harness for transport, authentication, account isolation, prelogin UI, server-config, sync, and cryptographic boundary tests;
- a deterministic static release builder with an explicit production-file allowlist, SHA-256 file identities, source-revision binding, and an explicit empty runtime-dependency inventory.

The sixth slice strengthens browser release evidence without changing credential handling:

- the deterministic release now emits an SPDX 2.3 JSON SBOM for the exact allowlisted browser files;
- every SBOM file record carries SHA-1, as required for analyzed files by SPDX 2.3, plus SHA-256 for GoreeVault integrity evidence;
- the package verification code is derived from the exact analyzed release files;
- SPDX creation time is bound to an explicit source-date epoch so rebuilding the same source with the same source timestamp produces identical evidence;
- `release-manifest.json` binds the SBOM path, byte size, SHA-256 digest, source revision, source timestamp, and explicit empty runtime-dependency inventory;
- file license and copyright conclusions remain `NOASSERTION` in the generated SBOM until the standalone GoreeVault Web repository establishes and validates its own final package-level licensing metadata.

These slices **do not** implement production credential processing, Argon2id account authentication, real password sign-in, production token exchange, end-to-end vault decryption, cipher CRUD, persistent encrypted cache, WebAuthn, attachments, organizations, TOTP, import/export, or persistent credential storage. Those features must be added only against the GoreeVault Web contract and compatible server protocol.

## Security boundary

The shell must not store or process production credentials yet. UI development must never introduce placeholder cryptography, fake encryption, plaintext vault persistence, or console logging of secrets simply to make screens appear functional.

Appearance is the only current browser-local preference. Account/session/authentication and opaque sync state remain in memory, and no reusable credentials or decrypted vault material are written to general browser storage. Prelogin handles only the normalized account identifier and server-provided KDF metadata; production password entry and secret-bearing network authentication remain disabled.

See `docs/SECURITY-BOUNDARY.md`.

## Validation

Run:

```sh
python3 web-client/tests/validate_web_shell.py
python3 -m unittest web-client/tests/test_build_release.py
cd web-client && npm test
python3 scripts/build_release.py --out /tmp/goreevault-web --source-revision local-validation --source-date-epoch 0
```

The validation gate checks local-only browser dependencies, required privacy/security metadata, Glaze UI/accessibility behavior, canonical runtime configuration, account/session isolation, disabled secret persistence, the fail-closed cryptography boundary, bounded API behavior, compatible prelogin metadata handling, stale-response rejection, disabled production token exchange, server identity/config negotiation, opaque sync isolation, deterministic release layout, source-bound manifest integrity, and SPDX SBOM integrity.

## Stable boundary

Creating these foundations does not close the GoreeVault product-wide Glaze UI or browser-readiness blockers. Stable still requires the standalone GoreeVault Web repository, reviewed Argon2id compatibility, complete end-to-end client cryptography, production sign-in/two-factor/token-refresh behavior, complete supported browser workflow matrix, real accessibility acceptance, immutable browser candidate publication, independent SBOM/dependency evidence from the final repository, migration/rollback proof, real-client testing, WebAuthn/passkey evidence, target-environment rehearsal, governance, and final exact-RC evidence.
