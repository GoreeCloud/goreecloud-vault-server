# GoreeVault Web Argon2id Browser Runtime Registration Contract

## Role and Purpose

I use this validation-only contract to prove the browser loading and explicit provider-handoff architecture for the GoreeVault-owned Argon2id WebAssembly implementation without adding the generated artifacts to the production browser release or enabling production credential processing.

This slice bridges the already validated `wasm-bindgen --target web` artifact evidence and the existing GoreeVault Argon2id provider boundary. It remains source-validation architecture only.

## Approval Boundary

The following states remain mandatory:

- production runtime registration: not approved;
- credential processing: not approved;
- automatic provider registration: disabled;
- production browser bundle inclusion: disabled;
- third-party WebAssembly origins: prohibited;
- mutable WebAssembly URLs with query strings or fragments: prohibited.

A successful test or GitHub Actions run does not change these approval states.

## Browser Loading Contract

The loader accepts an explicitly supplied generated-binding module loader and an explicitly supplied WebAssembly URL. It does not dynamically discover a provider, scan the page, read a remote manifest, or auto-register itself with authentication code.

Before initialization, the loader requires:

1. an HTTPS GoreeVault browser origin;
2. a WebAssembly URL resolving to that exact origin;
3. no URL credentials;
4. no query string or fragment;
5. a `.wasm` artifact path;
6. a generated `wasm-bindgen` default initializer;
7. the reviewed `derive_argon2id_wasm` export.

The generated default initializer receives the exact validated same-origin URL. Initialization errors propagate without retrying another origin, adding a fallback loader, or silently changing KDF behavior.

## Explicit Provider Handoff

After successful module initialization, the browser loader returns the already reviewed validation-only GoreeVault WebAssembly Argon2id provider. Returning a provider object is deliberately different from registering it automatically.

The caller must explicitly decide whether and where to pass that provider into a validation flow. The loader never mutates global authentication state and does not enable the master-password UI, password-grant transmission, production token exchange, or vault decryption.

## Security Properties

This architecture keeps the WebAssembly source same-origin and HTTPS-only and does not introduce a CDN, remote loader, blob URL, query-addressed mutable artifact, `unsafe-eval`, or a third-party runtime dependency.

The existing WebAssembly adapter continues to own and clear its JavaScript secret/salt copies, copy validated 32-byte output into independent caller memory, clear controllable generated-binding output, and propagate failures without PBKDF2 fallback for Argon2id accounts.

These controls reduce avoidable attack surface and secret lifetime but do not constitute real-browser memory-erasure proof.

## Release Separation

The loader lives under `web-client/validation/`. The generated browser JavaScript glue, WebAssembly artifact, runtime adapter, and browser loader remain outside the deterministic GoreeVault Web production release allowlist and outside `index.html`.

Promotion into the production release requires a separate reviewed change that updates immutable release identity and SPDX evidence for every promoted artifact.

## Remaining Production Acceptance

Before this architecture may become a production credential path, I must separately complete and retain at least:

- standalone GoreeVault Web repository ownership and independent release lifecycle;
- reviewed immutable browser release/SBOM inclusion for generated JavaScript and WebAssembly artifacts;
- final restrictive Content Security Policy validation with the promoted files;
- real supported-browser loading, memory, performance, compatibility, and accessibility evidence;
- complete password sign-in, supported two-factor flows, refresh/rotation, logout, and session invalidation;
- end-to-end account-key unwrap and supported vault encryption/decryption validation;
- real WebAuthn/passkey acceptance where supported;
- exact-server-candidate interoperability evidence;
- target-environment deployment, backup, restore, rollback, and monitoring rehearsal;
- repository governance controls;
- reversible browser cutover evidence;
- exact release-candidate evidence and final Stable authorization.

Until those requirements are complete, this browser loader and registration contract remains validation-only and must not process production credentials.
