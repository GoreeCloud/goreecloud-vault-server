# GoreeVault Web Argon2id Provider Boundary

## Status

**Pre-Alpha architecture boundary — no built-in Argon2id implementation is approved or enabled.**

## Role and Purpose

**Role:** Define the only supported integration seam for a future reviewed local Argon2id implementation used by GoreeVault Web authentication.

**Purpose:** Prevent GoreeVault Web from silently substituting PBKDF2, accepting incompatible Argon2id metadata, retaining provider inputs unnecessarily, or treating the existence of a provider interface as production credential-processing approval.

## Upstream compatibility basis

The provider contract is aligned to the current Bitwarden SDK implementation in `bitwarden/sdk-internal`, specifically `crates/bitwarden-crypto/src/keys/kdf.rs` and the `bitwarden-crypto` crate manifest reviewed for this boundary.

The reviewed upstream behavior is:

- RustCrypto `argon2` is pinned by Bitwarden to `0.6.0-rc.8` with `kdf` and `zeroize` features and default features disabled;
- the KDF algorithm is Argon2id;
- the Argon2 version is `0x13` (version 1.3);
- the server/API memory value is expressed in MiB and is multiplied by 1024 before it is passed to Argon2 as KiB;
- minimum accepted parameters are 2 iterations, 16 MiB memory, and parallelism 1;
- the normalized account identifier is SHA-256 hashed before it is supplied as the Argon2 salt;
- the derived output is exactly 32 bytes;
- the current upstream defaults are 6 iterations, 32 MiB memory, and parallelism 4.

GoreeVault Web keeps these semantics explicit at the provider boundary so a future implementation cannot accidentally interpret `kdfMemory` as KiB, use the normalized email directly as the Argon2 salt, use a different Argon2 version, or accept parameter values below the current Bitwarden minimums.

## Current boundary

`assets/argon2id-provider.js` establishes the following controls:

- no built-in Argon2id implementation is present;
- no PBKDF2 fallback is permitted for an Argon2id account;
- a provider must be created through the GoreeVault-owned provider factory before the KDF layer will use it;
- `kdfIterations` must be at least 2;
- `kdfMemory` must be at least 16 MiB and is converted to KiB before provider invocation;
- `kdfParallelism` must be at least 1;
- Argon2id version `0x13` is explicit in the provider request;
- the account identifier is normalized and then SHA-256 hashed before it becomes provider salt input;
- password, pre-hash salt-input, and hashed-salt byte buffers controlled by the JavaScript boundary are cleared after use;
- the provider must return an independent `Uint8Array` containing exactly 32 bytes;
- malformed provider output is cleared before rejection when possible;
- the derived master-key buffer is cleared by the authentication-material coordinator after the server authorization hash is produced;
- registering a provider does not change the browser runtime flag that keeps production credential processing disabled.

## Upstream interoperability vector

A future real provider must reproduce the current Bitwarden SDK Argon2id test vector before it can be considered for production authentication:

- password bytes: UTF-8 `67t9b5g67$%Dh89n`;
- salt input bytes: UTF-8 `test_key`;
- SHA-256 salt: `92488e1e3eeecdf99f3ed2ce59233efb4b4fb612d5655c0ce9ea52b5a502e655`;
- iterations: `4`;
- memory: `32 MiB` / `32768 KiB`;
- parallelism: `2`;
- algorithm/version: Argon2id / `0x13`;
- output length: `32` bytes;
- expected derived bytes, hex: `cff0e1b1a213a34c626ab3afe00911f01493ed2ff6968db83ee183f23335e1f2`.

This vector is for validating the low-level provider implementation. Production account preparation still requires a valid normalized GoreeVault account email and uses the SHA-256 digest of that normalized identifier as the Argon2 salt.

## Evidence requirement

A future real provider must not be treated as production-ready merely because it satisfies this JavaScript interface. Before it can be integrated into the production sign-in path, GoreeVault requires:

- a local/open implementation suitable for the approved browser release boundary;
- source and dependency review;
- the upstream Bitwarden Argon2id vector above plus retained GoreeVault interoperability vectors covering the supported parameter set;
- exact browser release and dependency/SBOM evidence;
- browser compatibility and performance acceptance on the supported matrix;
- secret-lifecycle review showing no password, master key, or derived key is written to general browser storage;
- final GoreeVault Web authentication and Stable evidence approval.

## Non-goals

This boundary does not implement the Argon2id algorithm. It only defines the controlled interface through which a separately reviewed implementation may later be admitted.

This boundary does not:

- enable master-password input;
- transmit a password grant;
- accept production tokens;
- unlock or decrypt a vault;
- authorize a browser cutover or Stable release.

The absence of a registered reviewed provider must continue to fail closed.
