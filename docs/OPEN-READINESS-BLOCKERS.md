# GoreeVault Open Readiness Blockers

## Purpose

This document tracks known GoreeVault release blockers that cannot be resolved solely by a successful source build or automated compatibility test.

It is an implementation tracker, not authorization to bypass `docs/PRODUCTION-READINESS.md`. A blocker remains open until the required evidence is completed and recorded against the exact candidate artifact.

## Current state

**Status:** Stable blocked

**Recorded:** August 15, 2026

The current server stabilization chain has strong automated compatibility, security, recovery, migration, deployment, release-image, Stable-evidence, and Glaze UI source checks. The following gates remain open.

## Blocker 1 — GitHub repository governance

### Current verified state

- GitHub repository rulesets endpoint returns no rulesets.
- GitHub Actions environments endpoint returns no environments.
- Classic `main` branch protection cannot be read through the current integration and remains unverified.
- Default GitHub Actions token permission state cannot be read through the current integration.
- Dependabot vulnerability-alert state cannot be read through the current integration.

### Required completion evidence

- protect `main` against direct/unreviewed release-source changes;
- enforce required GoreeVault release-blocking checks;
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

Run the supported real clients against the exact RC artifact and record version/platform/result evidence for:

- web;
- Chromium extension;
- Firefox extension;
- desktop;
- Android;
- CLI.

Each client must satisfy the checks defined by `docs/STABLE-EVIDENCE.md`.

## Blocker 3 — Real WebAuthn/passkey path

Complete and record at least one real supported browser/device/authenticator registration and authentication flow against the exact candidate.

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

No production activation should be inferred merely from completing a rehearsal.

## Blocker 5 — Product-wide Glaze UI ownership

The bundled upstream-compatible web vault remains a temporary development/compatibility dependency.

Under the current GoreeCloud mandatory Glaze UI baseline, Stable is blocked until GoreeVault owns the primary browser-vault presentation and product-wide Glaze UI conformance is proven.

The approved current path is GoreeVault Web as defined in `docs/ROADMAP.md`.

Required completion evidence includes:

- GoreeCloud-owned browser-vault application boundary;
- Glaze UI presentation throughout the controlled browser experience;
- System/Light/Dark behavior;
- keyboard/focus accessibility;
- reduced-motion and contrast/forced-colors handling;
- local-only presentation dependencies;
- no analytics/behavioral tracking;
- client-side zero-knowledge compatibility;
- real browser/accessibility acceptance evidence;
- compatibility tests against GoreeVault Server.

No permanent production Glaze exception is currently approved.

## Blocker 6 — Exact-RC Stable evidence

After all other Stable gates are complete:

- create schema-version-2 `goreevault-stable-evidence.json`;
- bind it to the exact RC tag, source SHA, and OCI manifest digest;
- validate it with `scripts/validate-stable-evidence.py`;
- attach it to the matching RC GitHub release;
- obtain the required release approval;
- only then create the Stable tag.

## Completion rule

Do not delete a blocker merely because work started or partial evidence exists. Mark it complete only when the applicable requirement is objectively satisfied and the final evidence is retained in the proper release or governance record.
