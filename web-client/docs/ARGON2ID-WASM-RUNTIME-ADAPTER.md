# GoreeVault Web Argon2id WASM Runtime Adapter

## Role and Purpose

I use the validation-only Argon2id WebAssembly runtime adapter to prove that GoreeVault Web's reviewed JavaScript provider boundary can call the exact generated `wasm-bindgen` ABI produced from the GoreeVault-owned RustCrypto Argon2id core.

This adapter is a source-validation component. It is not the production browser registration point and it does not authorize credential processing.

## Current Approval State

The following values remain mandatory:

- production runtime registration: not approved;
- automatic provider registration: disabled;
- credential processing: not approved;
- production browser bundle inclusion: not approved;
- PBKDF2 fallback for Argon2id accounts: prohibited.

A successful CI run does not change those approval states.

## ABI Contract

The adapter calls only the generated `derive_argon2id_wasm` export with:

1. encoded password bytes;
2. a 32-byte SHA-256 digest of the normalized account identifier;
3. Argon2id iterations;
4. memory converted from MiB to KiB;
5. parallelism.

The derived output must be exactly 32 bytes.

## Secret Lifecycle

The higher-level GoreeVault provider creates memory-only password and salt byte arrays and clears them after derivation. The runtime adapter creates independent JavaScript copies before entering the generated WebAssembly binding and clears those adapter-owned copies in all success and failure paths.

The Rust WebAssembly function receives Rust-owned copies through `wasm-bindgen` and zeroizes those copies before returning. When the generated JavaScript binding returns a controllable `Uint8Array`, the adapter copies it into independent caller-owned memory and clears the original returned buffer.

JavaScript and WebAssembly memory-management limitations mean these measures reduce avoidable secret lifetime but do not constitute proof that every historical memory copy has been physically erased. Real browser memory behavior remains a separate acceptance requirement.

## Failure Behavior

The adapter fails closed when:

- the generated module is missing;
- `derive_argon2id_wasm` is absent;
- the WebAssembly call throws;
- the returned value is not a `Uint8Array`;
- the returned value is not exactly 32 bytes.

WebAssembly failures propagate. The adapter does not silently retry with PBKDF2 or another KDF.

## Continuous Validation

The dedicated GoreeVault Web Argon2id Core workflow validates:

- the pinned Rust dependency graph;
- rustfmt and strict Clippy;
- native Bitwarden-compatible vectors;
- validation-only JavaScript adapter regression tests;
- wasm32 compilation;
- exact pinned `wasm-bindgen` CLI generation;
- the retained Bitwarden vector through the real generated ABI;
- the validation-only JavaScript adapter through the real generated binding;
- authentication-material equivalence through GoreeVault's KDF boundary;
- deterministic generated-binding evidence;
- deterministic build-only WebAssembly evidence.

The generated evidence must continue to record runtime integration and credential processing as unapproved.

## Production Promotion Requirements

Before this validation path can become an approved production browser provider, I must separately complete and retain at least:

- standalone GoreeVault Web repository ownership and release lifecycle;
- reviewed production loading and registration architecture;
- immutable browser release identity and SBOM coverage for the WebAssembly module and generated glue;
- restrictive Content Security Policy validation;
- supported-browser compatibility and performance testing;
- browser memory and secret-lifecycle review;
- complete sign-in, token, two-factor, logout, and session-invalidation validation;
- end-to-end zero-knowledge vault key unwrap and encryption/decryption validation;
- real browser accessibility and Glaze UI acceptance;
- exact-server-candidate compatibility evidence;
- reversible browser cutover and rollback proof;
- final GoreeVault release authorization.

Until those requirements are completed, this adapter remains validation-only.
