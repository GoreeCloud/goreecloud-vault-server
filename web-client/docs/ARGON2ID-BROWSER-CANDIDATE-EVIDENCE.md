# GoreeVault Web Argon2id Browser Candidate Evidence

## Purpose

This document defines the validation-only packaging boundary for the browser-target GoreeVault Argon2id WebAssembly module and generated `wasm-bindgen` glue.

The candidate package exists to prove deterministic artifact identity, exact source provenance, generator-version provenance, and SPDX coverage before any browser runtime or credential-processing approval is granted.

## Candidate contents

The candidate evidence builder accepts only generated files whose names begin with `goreevault_web_argon2id_core` and requires, at minimum:

- `goreevault_web_argon2id_core.js`;
- `goreevault_web_argon2id_core_bg.wasm`.

The builder rejects symlinks, unexpected filenames, unsupported file types, missing required files, an unverified source revision, and a missing `wasm-bindgen` version.

For every accepted generated file, the candidate manifest records the filename, byte size, and SHA-256 identity. The associated SPDX 2.3 document records SHA-1 and SHA-256 file identities and binds the package to the exact source revision.

## Mandatory fail-closed approvals

Every generated candidate manifest must record:

- `runtimeIntegrationApproved: false`;
- `credentialProcessingApproved: false`;
- `productionReleaseInclusionApproved: false`.

The evidence builder does not provide a command-line switch or environment variable that can change those values.

## Production separation

The generated JavaScript and WebAssembly files remain outside `web-client/scripts/build_release.py` and therefore outside the current deterministic GoreeVault Web production release allowlist.

The dedicated `GoreeVault Web Argon2id Candidate Evidence` workflow independently regenerates browser bindings, builds the validation-only candidate, verifies its hashes and SPDX document, asserts all approval flags remain false, and confirms the generated runtime files remain absent from the production release builder.

## What this evidence proves

This evidence proves that an exact source revision can produce an independently identifiable browser crypto candidate whose generated files and SPDX metadata are retained as a coherent validation artifact.

It does not prove browser runtime compatibility, CSP acceptance, acceptable secret-memory behavior, production authentication correctness, release approval, or Stable readiness.

## Remaining promotion requirements

Before these generated artifacts may enter a production GoreeVault Web release, the project still requires reviewed production runtime registration, real-browser CSP/performance/memory/compatibility evidence, complete authentication and zero-knowledge workflow validation, immutable final release/SBOM evidence, rollback proof, and the other applicable requirements in `docs/OPEN-READINESS-BLOCKERS.md` and `docs/PRODUCTION-READINESS.md`.
