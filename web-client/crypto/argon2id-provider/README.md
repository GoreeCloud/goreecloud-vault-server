# GoreeVault Web Argon2id Rust Core

## Status

**Pre-Alpha — build and interoperability validation only. Not wired to the browser runtime or production release.**

## Role and Purpose

**Role:** GoreeVault-owned low-level Argon2id derivation core for the future GoreeVault Web provider.

**Purpose:** Reproduce the reviewed Bitwarden-compatible Argon2id primitive with a small, auditable, open-source dependency surface before any JavaScript/WASM ABI or production credential path is approved.

## Dependency choice

The core pins:

- `argon2 = 0.6.0-rc.8`, the same RustCrypto Argon2 release currently pinned by Bitwarden's `bitwarden-crypto` crate;
- default Argon2 crate features disabled;
- only the `kdf` and `zeroize` features enabled.

RustCrypto Argon2 `0.6.0-rc.8` is licensed `MIT OR Apache-2.0`. GoreeVault therefore does not need to import Bitwarden's broader `bitwarden-crypto` package, whose crate-level licensing and larger SDK surface are unnecessary for this isolated primitive.

The GoreeVault core itself remains `AGPL-3.0-only` while it lives inside `goreevault-server`.

## Compatibility contract

The Rust core accepts only an already SHA-256-hashed 32-byte account salt and explicit Argon2 parameters. Account normalization, SHA-256 salt preparation, and MiB-to-KiB conversion remain owned by the reviewed JavaScript provider boundary.

The core enforces:

- Argon2id;
- version `0x13`;
- exactly 32 output bytes;
- minimum 2 iterations;
- minimum 16384 KiB memory;
- minimum parallelism 1;
- the current Bitwarden Argon2id interoperability vector;
- a post-derivation 4 KiB stack overwrite matching Bitwarden's current defensive cleanup pattern.

## Browser/WASM boundary

The crate is configured as both `rlib` and `cdylib`, and CI compiles it for `wasm32-unknown-unknown` to prove the selected primitive is compatible with the intended browser target.

**There is intentionally no JavaScript binding yet.** No `wasm-bindgen` API is exported and no `.wasm` file is copied into the GoreeVault Web deterministic release allowlist. This prevents a buildable cryptographic primitive from becoming an approved credential-processing path before the JS↔WASM copy, allocation, cleanup, CSP, and artifact-evidence boundaries are reviewed.

A later binding slice must independently validate:

- JS/WASM input-copy behavior;
- password, salt, derived-key, and temporary-allocation cleanup limits;
- generated glue code and CSP behavior;
- exact locked Rust dependency graph;
- deterministic WASM build identity and SBOM inclusion;
- browser performance and memory use across the supported matrix;
- the Bitwarden vector through the actual browser ABI;
- failure behavior with no PBKDF2 fallback.

## Validation

The dedicated workflow performs:

```sh
cargo generate-lockfile
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
rustup target add wasm32-unknown-unknown
cargo check --target wasm32-unknown-unknown
```

The generated `Cargo.lock` is printed with its SHA-256 identity during the first validation cycle so the exact transitive dependency graph can be reviewed and committed before browser integration.
