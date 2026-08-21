# GoreeCloud Vault Server Open Readiness Blockers

## Purpose

This document tracks known GoreeCloud Vault Server release blockers that cannot be resolved solely by a successful source build or automated compatibility test.

It is an implementation tracker, not authorization to bypass `docs/PRODUCTION-READINESS.md`. A blocker remains open until the required evidence is completed and recorded against the exact candidate artifact.

`GoreeVault` remains the broader client-family and historical product identity. GoreeVault Web and compatibility-era evidence filenames retain that identity unless a separate client-family naming decision changes them.

## Current state

**Status:** Stable blocked

**Recorded:** August 21, 2026

The current server stabilization chain has strong automated compatibility, security, recovery, migration, deployment, release-image, Stable-evidence, Glaze UI, repository-readiness, and evidence-tooling source checks. GoreeVault Web also has a Glaze UI incubation shell, deterministic release/SBOM evidence, a client SDK boundary, fail-closed prelogin/authentication architecture, a reviewed Rust Argon2id core, build-only WebAssembly identity evidence, an isolated WebAssembly ABI/binding validation path, and a validation-only JavaScript runtime adapter exercised against the actual generated bindings and GoreeVault authentication-material derivation. None of those source milestones substitutes for the real-world gates below.

## Blocker 1 — GitHub repository governance

### Current verified state

- GitHub repository rulesets endpoint returns no rulesets.
- GitHub Actions environments endpoint returns no environments.
- `main` is currently reported by GitHub as unprotected.
- Default GitHub Actions token permission state cannot be read through the current integration.
- Dependabot vulnerability-alert state cannot be read through the current integration.

### Required completion evidence

- protect `main` against direct/unreviewed release-source changes;
- enforce required GoreeCloud Vault Server release-blocking checks;
- enforce CODEOWNERS review for protected surfaces;
- create the protected `release` environment;
- require at least one release reviewer;
- prevent self-review where supported;
- verify read-only default Actions permissions;
- enable/verify Dependabot vulnerability alerts;
- verify secret scanning, push protection, and private vulnerability reporting where supported;
- record the verified state in the exact-RC Stable evidence record.

The current GitHub connector does not expose the write operations needed to create these repository settings, so they require an approved GitHub administrative action outside the repository source change.

## Blocker 2 — Real supported-client matrix

Run the supported real clients against the exact GoreeCloud Vault Server RC artifact and record version/platform/result evidence for:

- web;
- Chromium extension;
- Firefox extension;
- desktop;
- Android;
- CLI.

Each client must satisfy the checks defined by `docs/STABLE-EVIDENCE.md`.

## Blocker 3 — Real WebAuthn/passkey path

Complete and record at least one real supported browser/device/authenticator registration and authentication flow against the exact GoreeCloud Vault Server candidate.

Synthetic challenge/rejection coverage remains valuable but does not close this blocker.

## Blocker 4 — Target-environment production rehearsal

Exercise the reviewed production contract in the intended GoreeCloud target environment with exact immutable digests and verify:

- loopback-only backend publication;
- trusted reverse-proxy HTTPS/WSS;
- internal-only PostgreSQL networking;
- non-root/capability-free/read-only-root runtime;
- closed registration and disabled `/admin` policy;
- pre-change backup;
- verified restore;
- recorded rollback;
- monitoring and certificate/storage/restart visibility;
- privacy-conscious logging;
- approved private administrative access path.

### Tooling status

`scripts/collect-target-evidence.py` now provides a read-only, secret-minimizing collector for the Stable record's `target_environment` section. It machine-checks the controls that can be observed safely from the reviewed production source, Docker metadata, immutable image references, and the canonical HTTPS health endpoint. Controls such as real HTTPS/WSS validation, backup/restore, rollback, monitoring, log review, and NetBird path verification require explicit operator attestations after the work is actually completed.

The collector does not run a deployment, create a backup, perform a restore, change Docker state, alter Caddy/NetBird, or close this blocker by itself.

No production activation should be inferred merely from completing a rehearsal or generating a passing JSON section.

## Blocker 5 — Product-wide Glaze UI ownership and GoreeVault Web completion

The bundled upstream-compatible web vault remains a temporary development/compatibility dependency.

Under the current GoreeCloud mandatory Glaze UI baseline, Stable is blocked until GoreeCloud owns the primary browser-vault presentation and product-wide Glaze UI conformance is proven.

The approved current path is GoreeVault Web as defined in `docs/ROADMAP.md`.

### Current implementation status

`docs/WEB-CLIENT-CONTRACT.md` defines the GoreeVault Web Role and Purpose, server/client ownership boundary, client-side zero-knowledge rules, multi-user browser isolation, browser storage policy, compatible workflow baseline, Glaze UI requirements, accessibility acceptance, CSP/dependency direction, privacy/telemetry rules, immutable release evidence, and reversible migration/fallback requirements.

The temporary `web-client/` incubation boundary now includes a GoreeCloud-owned GoreeVault Web Glaze UI application shell, deterministic static release/SPDX evidence, a GoreeVault client SDK facade, SDK-backed email-only prelogin, account-scoped memory-only session/sync foundations, reviewed PBKDF2 and low-level vault-cryptography primitives, a fail-closed Argon2id provider contract, a pinned RustCrypto Argon2id core, exact build-only WebAssembly identity evidence, an isolated pinned `wasm-bindgen` ABI path with deterministic generated-binding evidence, and a validation-only JavaScript runtime adapter. The adapter copies and clears caller-controlled secret/salt buffers, clears controllable generated-binding output after copying it into independent memory, propagates failures without PBKDF2 fallback, and is continuously exercised against the actual generated `wasm-bindgen` module and GoreeVault authentication-material derivation. Production registration, browser-bundle inclusion, and credential processing remain explicitly unapproved.

The planned standalone `GoreeCloud/goreevault-web` repository has not yet been created. The current GitHub connector cannot create repositories, so this source-separation requirement remains open rather than being simulated inside the server repository.

Remaining completion evidence includes:

- standalone GoreeCloud-owned browser-vault repository and independent release lifecycle;
- reviewed production browser loading and runtime registration of the Argon2id provider;
- immutable browser release/SBOM coverage for the final WebAssembly module and generated glue;
- real browser performance, memory, CSP, and compatibility evidence for the generated WebAssembly path;
- complete supported sign-in, two-factor, token refresh/rotation, logout, and session invalidation;
- end-to-end user/account key unwrap and supported vault encryption/decryption workflows;
- item create/update/delete, attachments, organization/collection boundaries, TOTP, import/export, and required error/offline behavior;
- Glaze UI presentation throughout the controlled browser experience;
- System/Light/Dark behavior;
- keyboard/focus accessibility;
- reduced-motion and contrast/forced-colors handling;
- local-only presentation dependencies;
- no analytics/behavioral tracking;
- real browser/accessibility acceptance evidence;
- compatibility tests against the exact GoreeCloud Vault Server candidate;
- reversible migration/cutover and previous-known-good browser rollback proof.

No permanent production Glaze exception is currently approved.

## Blocker 6 — Exact-RC Stable evidence

After all other Stable gates are complete:

- create schema-version-2 `goreevault-stable-evidence.json`;
- bind it to the exact GoreeCloud Vault Server RC tag, source SHA, and OCI manifest digest;
- validate it with `scripts/validate-stable-evidence.py`;
- attach it to the matching RC GitHub release;
- obtain the required release approval;
- only then create the Stable tag.

The compatibility-era evidence filename is intentionally retained by current tooling and does not represent the canonical server name.

The target-environment collector may provide only the `target_environment` object. It must not be treated as a complete Stable evidence file or as approval for any other section.

## Completion rule

Do not delete a blocker merely because work started or partial evidence exists. Mark it complete only when the applicable requirement is objectively satisfied and the final evidence is retained in the proper release or governance record.
