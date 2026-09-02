# GoreeCloud Vault Server Repository Structure

## Purpose

This document defines the source-control structure of GoreeCloud Vault Server and the responsibility boundary of each major repository area.

The repository now contains two deliberately separate server implementation lines:

1. `native/` — the original GoreeCloud-owned server implementation and canonical long-term product direction.
2. `src/` plus inherited migrations/build structures — the transitional Vaultwarden-compatible runtime retained for compatibility, migration, rollback, and behavioral reference until the native server satisfies its required acceptance gates.

`GoreeVault` remains the broader client-family and historical product identity. Compatibility-era internal identifiers are not renamed solely for branding when doing so would add protocol, migration, security, or recovery risk.

## Structural principles

1. Native GoreeCloud product logic belongs in `native/`, not in a new layer that copies inherited application architecture.
2. Retain compatibility-sensitive inherited code only as long as it has a documented migration, rollback, interoperability, or recovery purpose.
3. Narrow critical dependencies may be retained when reimplementation would materially increase cryptographic, protocol, database, runtime, standards, or interoperability risk.
4. Do not create a top-level directory merely for visual organization; every top-level component needs a durable role, ownership boundary, security/privacy model, data boundary, dependency model, validation model, and retirement path.
5. Keep reusable secrets and private production values outside the repository.
6. Use synthetic identities and data in tests. Production vault exports, passwords, credentials, private databases, backups, tokens, recovery codes, and private user content are prohibited ordinary fixtures.
7. Keep generated files traceable to their generator and exact source inputs.
8. Keep release-blocking validators deterministic and dependency-light where practical.
9. Treat repository documentation as an implementation companion to authoritative GoreeCloud project governance, not a replacement for it.
10. Keep source acceptance, release acceptance, and production acceptance separate.
11. Glaze UI, Wardveil Security, Privacy Shield, and Everkeep are mandatory Stable gates; GoreeCloud Identity and GoreeCloud Mesh must be implemented where applicable rather than represented by naming only.

## Top-level layout

### `.github/`

Repository automation and review governance.

Includes GitHub Actions, CODEOWNERS, pull-request policy, release validation, security validation, compatibility, recovery, deployment, evidence tooling, and repository-readiness automation.

Changes here are security-sensitive because workflows may affect release publication, registry access, evidence collection, or repository permissions.

All GoreeCloud-owned workflows must follow the repository workflow-security contract, including explicit permissions, immutable external-action pins, and non-persisted checkout credentials.

### `native/`

Original GoreeCloud-owned Vault Server implementation.

The native directory is a durable product-architecture boundary, not an organizational mirror of inherited source.

The first native crate:

- is isolated from the root inherited Cargo workspace with an empty `[workspace]` declaration;
- uses the repository-pinned Rust toolchain;
- currently has no third-party runtime dependencies;
- models production readiness fail closed;
- stores only bounded opaque encrypted bytes in a development-only memory store;
- tests owner isolation with synthetic identities;
- exposes no network API or production authentication;
- is validated by a dedicated exact-head workflow.

Future native components belong here only after their role, security/privacy impact, data ownership, authentication/authorization model, dependency model, recovery impact, and migration relationship are documented.

### `deploy/`

Reviewed transitional production deployment contract.

This directory currently describes the compatibility runtime deployment model. It must not be treated as a native production deployment contract until a separate native deployment design and acceptance path are integrated.

Production deployment files must preserve immutable image references, private backend publication, database isolation, least privilege, secret separation, backup/recovery requirements, and trusted reverse-proxy boundaries.

### `docker/`

Transitional compatibility container-build sources and generated image definitions.

These files remain relevant while the inherited runtime is used for compatibility and migration. They are not the default architecture template for the native server.

Generated Dockerfiles must be changed through their documented source/generator path.

### `docs/`

Implementation, architecture, security, compatibility, operational, release, client-boundary, migration, and governance records.

Important documents include:

- `SERVER-IDENTITY.md` — canonical server identity and naming boundary;
- `GLAZE-UI.md` — server-owned Glaze UI implementation contract;
- `WEB-CLIENT-CONTRACT.md` — GoreeVault Web client boundary;
- `PRODUCTION-READINESS.md` — RC and Stable gates;
- `PRODUCTION-DEPLOYMENT.md` — reviewed transitional deployment contract;
- `SECURITY-MODEL.md` — security and zero-knowledge boundaries;
- `STABLE-EVIDENCE.md` — machine-readable Stable evidence contract;
- `UPSTREAM.md` — upstream synchronization, provenance, and transitional-reference expectations;
- `ROADMAP.md` — staged product direction;
- `OPEN-READINESS-BLOCKERS.md` — unresolved exact-candidate gates;
- `REPOSITORY-STRUCTURE.md` — this document.

Repository documentation must not store reusable credentials, production secrets, decrypted vault data, private user content, or sensitive recovery material.

### `migrations/`

Transitional Vaultwarden-compatible database migrations.

Migration changes remain release-critical while the compatibility runtime is supported.

A future native persistence model must not silently inherit this schema. Native schema adoption requires a separately reviewed owner-isolation, migration, rollback, compatibility, and Everkeep recovery design.

### `scripts/`

GoreeCloud-owned and inherited automation used for development, validation, security, compatibility, deployment, release, recovery, migration, and evidence checks.

Release-blocking scripts should fail closed on missing or malformed required state. Validation-only scripts must not silently mutate production.

Read-only evidence collectors must minimize output and must not serialize full container environments, reusable credentials, vault contents, or other unnecessary private data.

### `src/`

Transitional Vaultwarden-compatible Rust server runtime and compatibility-era server-owned presentation.

This directory remains security-sensitive and operationally important while migration is incomplete, but it is not the canonical long-term GoreeCloud product architecture.

Internal `vaultwarden` names may remain where renaming them would unnecessarily increase protocol, database, build, migration, or upstream-reference risk.

No new general native application architecture should be added here merely because inherited code already exists.

### `tests/`

Release-blocking compatibility, recovery, migration, deployment, security, and evidence-tooling coverage.

Tests must use synthetic identities and data. Production databases, vault exports, passwords, credentials, backups, recovery material, and private user content are prohibited ordinary fixtures.

Native Rust unit tests live with the native crate when that keeps the first-party boundary clear.

### `web-client/`

Temporary GoreeVault Web incubation boundary.

This client owns a separate browser-side cryptographic, storage, dependency, release, accessibility, and Glaze UI lifecycle and must move to its dedicated client repository before Stable promotion under the current project direction.

The server repository may retain explicit client integration contracts and migration evidence, but the browser client is not server runtime architecture.

## Root product records

### `README.md`

Public entry point. It must describe the native-first GoreeCloud direction, preserve the client-family naming boundary, identify inherited Vaultwarden code as transitional compatibility/migration material, and keep the non-Stable production boundary explicit.

### `SPECIFICATIONS.md`

Current server requirements and implemented/native versus transitional boundaries.

### `FEATURES.md`

Current implemented functionality. Planned or transitional compatibility capability must not be misrepresented as native implementation.

### `BENEFITS.md`

Product and architecture benefits grounded in current direction and implemented controls.

### `COMPETITIVE-OBJECTIVES.md`

Long-term objectives and acceptance criteria. Objectives are not feature-completion claims.

### `BRANDING.md`

Canonical product presentation and brand constraints.

### `GOREVAULT.md`

Historical product-family, provenance, compatibility, and transition record. The filename is retained for continuity; current content must follow the canonical server identity and native-development direction.

### `CONTRIBUTING.md`

Contributor expectations and validation requirements.

### `SECURITY.md`

Vulnerability reporting and security support boundary.

### Root Cargo/build files

`Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, `build.rs`, Docker generation files, and related inherited build inputs remain part of the transitional compatibility runtime unless a native document explicitly adopts them.

The repository-wide `rust-toolchain.toml` is also the pinned toolchain authority for the independent native crate.

## UI ownership boundary

Server-owned user-facing surfaces must use current Glaze UI requirements.

The primary browser vault is a separate GoreeVault client lifecycle because it owns client-side cryptography, browser storage, dependency graph, build pipeline, compatibility matrix, release lifecycle, and full Glaze UI presentation.

The bundled upstream-compatible browser vault remains a transitional compatibility dependency and does not satisfy product-wide Glaze UI acceptance.

The current native server foundation has no user-facing UI.

## Multi-user boundary

GoreeCloud Vault Server is a multi-user credential service.

Native and transitional changes must preserve or improve:

- individual user identity;
- private-vault isolation;
- authorization on user-owned resources;
- organization and collection permissions;
- safe member lifecycle behavior;
- session/device revocation;
- separation of private-network reachability from application authorization.

Cross-user data exposure is a release blocker.

## Adding a native component

Before adding a new native module, service, dependency, persistent store, network API, client integration, or top-level component, document:

- Role and Purpose;
- ownership and maintenance boundary;
- security and privacy impact;
- data ownership and authoritative storage;
- authentication and authorization model;
- dependency and update model;
- logging/telemetry behavior;
- GoreeCloud Identity and Mesh applicability;
- Glaze UI, Wardveil Security, Privacy Shield, and Everkeep applicability;
- backup/recovery impact;
- release and testing model;
- migration, rollback, and retirement path.

Prefer the smallest structure that keeps those boundaries explicit and recoverable.
