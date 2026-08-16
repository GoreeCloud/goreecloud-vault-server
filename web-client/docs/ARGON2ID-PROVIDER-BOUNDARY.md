# GoreeVault Web Argon2id Provider Boundary

## Status

**Pre-Alpha architecture boundary — no built-in Argon2id implementation is approved or enabled.**

## Role and Purpose

**Role:** Define the only supported integration seam for a future reviewed local Argon2id implementation used by GoreeVault Web authentication.

**Purpose:** Prevent GoreeVault Web from silently substituting PBKDF2, accepting incomplete Argon2id metadata, retaining provider inputs unnecessarily, or treating the existence of a provider interface as production credential-processing approval.

## Current boundary

`assets/argon2id-provider.js` establishes the following controls:

- no built-in Argon2id implementation is present;
- no PBKDF2 fallback is permitted for an Argon2id account;
- a provider must be created through the GoreeVault-owned provider factory before the KDF layer will use it;
- `kdfIterations`, `kdfMemory`, and `kdfParallelism` must all be positive integers;
- the account identifier is normalized before it becomes provider salt input;
- password and salt byte buffers supplied to the provider are cleared after the provider call returns or throws;
- the provider must return an independent `Uint8Array` containing exactly 32 bytes;
- malformed provider output is cleared before rejection when possible;
- the derived master-key buffer is cleared by the authentication-material coordinator after the server authorization hash is produced;
- registering a provider does not change the browser runtime flag that keeps production credential processing disabled.

## Evidence requirement

A future real provider must not be treated as production-ready merely because it satisfies this JavaScript interface. Before it can be integrated into the production sign-in path, GoreeVault requires:

- a local/open implementation suitable for the approved browser release boundary;
- source and dependency review;
- retained Bitwarden/GoreeVault interoperability vectors covering the supported Argon2id parameter set;
- exact browser release and dependency/SBOM evidence;
- browser compatibility and performance acceptance on the supported matrix;
- secret-lifecycle review showing no password, master key, or derived key is written to general browser storage;
- final GoreeVault Web authentication and Stable evidence approval.

## Non-goals

This boundary does not:

- implement the Argon2id algorithm;
- enable master-password input;
- transmit a password grant;
- accept production tokens;
- unlock or decrypt a vault;
- authorize a browser cutover or Stable release.

The absence of a registered reviewed provider must continue to fail closed.
