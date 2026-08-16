# GoreeVault Web Security Boundary

## Current state

GoreeVault Web is pre-alpha. The current implementation is an application shell plus fail-closed client and protocol foundations and must not be used with real vault credentials.

## Non-negotiable rules

- Do not invent cryptographic primitives.
- Do not persist master passwords, plaintext vault items, derived keys, decrypted attachments, TOTP seeds, recovery codes, bearer tokens, or refresh tokens in general browser storage.
- Do not log secrets to the browser console, DOM diagnostics, telemetry, crash reports, URLs, or analytics events.
- Do not add analytics, advertising, fingerprinting, remote fonts, third-party browser scripts, or a hosted control plane for ordinary operation.
- Treat NetBird/private-network reachability as transport access only; it is not application authorization.
- Keep all account/session and vault state explicitly scoped to the selected GoreeVault identity.
- Clear decrypted state and key material on lock, logout, account switch, account removal, and session invalidation.
- Service workers must not cache authenticated private API responses unless the representation is encrypted and separately reviewed.
- Keep reusable authentication tokens out of general browser storage until the approved compatible session model and storage controls are implemented and reviewed.

## Current protocol boundary

Server capability verification and prelogin are the only authentication-preparation interactions authorized in this implementation slice. The client may request `/api/config` to verify GoreeVault server identity and the approved production environment, then send the normalized account email identifier to `/api/accounts/prelogin` and accept only the compatible KDF metadata required to prepare a future client-side sign-in flow: `kdf`, `kdfIterations`, `kdfMemory`, and `kdfParallelism`.

The prelogin response does not authorize password derivation or sign-in. Account-scoped request epochs must reject stale responses after an account change or authentication reset. The Glaze UI contains no password input and must not add one while credential processing remains disabled.

The compatible password-grant fields, two-factor challenge shape, token-rotation requirement, and sync-envelope shape may be modeled and tested without transmitting secrets. This structural modeling does not authorize a secret-bearing request.

Real password entry remains disabled. Master-password processing, KDF execution, password-hash generation, access-token acceptance, refresh-token exchange, refresh-token persistence, authenticated sync, vault unlock, and secret-bearing authentication requests are outside the current approved slice.

Browser API requests must remain abortable and timeout-bounded, avoid general browser caching, reject redirects, and avoid broader credential scope than the selected GoreeVault origin requires. Normalized errors must not expose or log secret request material.

## Opaque sync boundary

GoreeVault Web may structurally validate the compatible `/api/sync` response and hold that response temporarily as opaque account-scoped memory for testing the client architecture. The current implementation must not request authenticated sync because token acceptance is disabled.

Opaque sync state must:

- remain memory-only;
- be bound to one explicit account identity and state epoch;
- reject stale state after an account change;
- reject cross-account state assignment;
- remain encrypted/opaque where the server payload contains encrypted vault fields;
- never be treated as authorization to decrypt or render private vault contents;
- never be persisted to IndexedDB, Cache Storage, localStorage, sessionStorage, or filesystem APIs in this pre-alpha slice.

Persistent encrypted caching, offline support, authenticated sync transport, and decrypted-item state require separate implementation and review.

## Release-artifact boundary

The incubation client may produce a deterministic static release layout for validation. The release builder must use an explicit file allowlist, bind the manifest to the source revision, record SHA-256 identities for shipped files, and exclude development tests and documentation from the browser publication tree.

A deterministic incubation build is not by itself a Stable release artifact. Stable still requires the dedicated GoreeVault Web repository and release lifecycle, immutable candidate publication, dependency inventory/SBOM, exact-server compatibility evidence, browser acceptance, and rollback evidence.

## Implementation sequencing

The application shell and non-secret protocol boundaries may be developed before full protocol integration. Authentication, key derivation, vault encryption/decryption, persistent encrypted storage, WebAuthn/passkey flows, authenticated sync, attachments, organizations, TOTP, import/export, and offline behavior must each be implemented against the documented GoreeVault Server compatibility baseline and reviewed security model.

UI prototypes must remain obviously non-functional where secure protocol behavior is not implemented. A visual mock must never masquerade as working credential security.

## Content Security Policy direction

The production client must remain compatible with a restrictive CSP using local application assets and avoiding `unsafe-eval`. Any future requirement for `unsafe-inline`, third-party script/style origins, remote fonts, or broad `connect-src` entries requires explicit security review and a removal plan.

## Production boundary

This incubation directory must move to the dedicated GoreeVault Web repository before Stable so browser dependencies, releases, SBOMs, immutable artifacts, compatibility evidence, and rollback records have their own lifecycle and review boundary.
