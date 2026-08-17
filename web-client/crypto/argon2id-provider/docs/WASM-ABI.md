# GoreeVault Web Argon2id WASM ABI

## Status

Pre-alpha. Build and interoperability validation only. Browser runtime registration and production credential processing remain unapproved.

## Purpose

This boundary exposes the reviewed GoreeVault Rust Argon2id primitive through a single `wasm-bindgen` function so GoreeVault can prove actual JavaScript-to-WebAssembly interoperability before any authentication path is enabled.

## Export

`derive_argon2id_wasm(secret, salt_sha256, iterations, memory_kib, parallelism)`

The export accepts:

- already UTF-8-encoded master-password bytes;
- exactly 32 bytes containing SHA-256 of the normalized account identifier;
- Argon2id iterations;
- Argon2id memory in KiB;
- Argon2id parallelism.

It returns exactly 32 derived bytes when successful.

## Security boundary

The ABI does not normalize account identifiers, hash the account salt, retain credentials, exchange tokens, decrypt vault material, register itself with `argon2id-provider.js`, or enable the browser credential-processing gate.

Rust-owned copies of the secret and salt are zeroized before the ABI returns. The JavaScript caller remains responsible for clearing caller-owned buffers under the existing provider contract.

Errors cross the ABI as stable, non-secret codes only:

- `invalid-salt-length`
- `insufficient-parameters`
- `invalid-parameters`
- `derivation-failed`

## Validation

CI builds the crate for `wasm32-unknown-unknown`, runs the exact pinned `wasm-bindgen` CLI, and invokes the generated Node.js binding with the retained Bitwarden interoperability vector. The same gate proves invalid salt lengths and below-minimum KDF parameters fail closed.

The generated bindings are validation artifacts only and are not part of the deterministic GoreeVault Web release allowlist.
