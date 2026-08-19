# GoreeVault Web Argon2id Browser-Binding Evidence

## Role and Purpose

I use this validation slice to prove that the reviewed GoreeVault RustCrypto Argon2id WebAssembly core can produce deterministic browser-target `wasm-bindgen` artifacts whose identities are retained as source-bound evidence.

This work is validation-only. It does not make the generated browser artifacts part of the GoreeVault Web production release and it does not authorize browser credential processing.

## Generated Target

The dedicated GoreeVault Web Argon2id Core workflow uses the exact pinned `wasm-bindgen-cli` version already required by the Node.js ABI validation path and separately runs `wasm-bindgen --target web` against the exact compiled WebAssembly module.

The generated browser directory is isolated under the GitHub Actions runner temporary directory. It is not copied into `web-client/assets`, `web-client/dist`, or another production browser source directory.

## Deterministic Evidence

The existing fail-closed binding-evidence generator inventories every generated browser-target artifact and records:

- relative artifact path;
- byte size;
- SHA-256 identity;
- exact 40-character source revision;
- exact `wasm-bindgen-cli` version;
- `runtimeIntegrationApproved: false`;
- `credentialProcessingApproved: false`.

Empty binding directories and empty generated artifacts fail validation.

## Production Release Separation

The validation workflow explicitly verifies that the browser-target generated JavaScript, WebAssembly module, and validation adapter remain absent from the deterministic GoreeVault Web production release allowlist and from `index.html`.

The current release builder therefore continues to describe only the intentionally allowlisted pre-alpha browser shell files. Browser-target Argon2id artifacts require a separate reviewed promotion before they may be included in release identity or SBOM evidence.

## Content Security Policy Boundary

This slice does not weaken or modify the existing GoreeVault Web Content Security Policy. It does not add remote script origins, remote WebAssembly sources, blob execution, `unsafe-eval`, or a third-party loader.

Generating `--target web` bindings proves artifact generation and identity only. It does not prove that the final browser loading architecture satisfies every supported browser's WebAssembly and CSP behavior.

## Remaining Browser Acceptance

Before the browser-target binding can be promoted into a production credential path, I must separately complete and retain:

- reviewed production module loading and explicit Argon2id provider registration;
- deterministic release/SBOM inclusion for the promoted JavaScript and WebAssembly artifacts;
- supported-browser CSP validation using the final release files;
- real browser compatibility, performance, and memory-lifecycle evidence;
- complete password sign-in, two-factor, refresh, logout, and invalidation behavior;
- end-to-end key unwrap and vault encryption/decryption validation;
- exact-server-candidate interoperability evidence;
- reversible browser cutover and rollback evidence;
- required release and Stable authorization.

Until those requirements are complete, generated browser bindings remain isolated validation artifacts and must not be interpreted as permission to process production credentials.
