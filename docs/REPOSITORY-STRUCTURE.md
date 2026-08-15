# GoreeVault Repository Structure

## Purpose

This document defines the source-control structure of GoreeVault Server and the responsibility boundary of each major repository area.

The structure is intended to keep the maintained Vaultwarden compatibility core understandable while making GoreeCloud-owned security, deployment, release, Glaze UI, and governance work easy to locate and review.

## Structural principles

1. Keep compatibility-sensitive server code close to the upstream layout unless a different structure provides a clear security or maintenance benefit.
2. Keep GoreeCloud-owned validation, deployment, governance, and product documentation explicit rather than hiding it inside upstream files.
3. Do not create new top-level directories merely for visual organization; a directory should represent a durable ownership, build, runtime, or lifecycle boundary.
4. Keep reusable secrets and private production values outside the repository.
5. Keep generated files traceable to their generator/source inputs.
6. Keep release-blocking validators deterministic and dependency-light where practical.
7. Treat repository documentation as an implementation companion to authoritative GoreeCloud governance records, not as a replacement for those records.

## Top-level layout

### `.github/`

Repository automation and review governance.

Includes:

- GitHub Actions workflows;
- CODEOWNERS;
- pull-request and issue configuration where applicable;
- release, security, compatibility, recovery, deployment, Glaze UI, and repository-readiness automation.

Changes here are security-sensitive because workflows may control release publication, registry access, evidence collection, or repository permissions.

### `deploy/`

GoreeCloud-owned production deployment contract.

This directory is separate from upstream development examples. Production deployment files must preserve immutable image references, private backend publication, database isolation, least privilege, backup/recovery requirements, and the canonical GoreeCloud service origin.

### `docker/`

Container build sources and generated image build definitions.

The repository retains upstream-compatible Docker generation where practical. Generated Dockerfiles must be changed through their documented source/generator path when the upstream build process requires it.

The root `Dockerfile` and generated Dockerfiles are build inputs, not production deployment manifests. Production runtime policy belongs in `deploy/`.

### `docs/`

GoreeVault implementation, architecture, security, compatibility, operational, release, and governance records.

Important documents include:

- `GLAZE-UI.md` — repository Glaze UI implementation contract;
- `PRODUCTION-READINESS.md` — RC and Stable gates;
- `PRODUCTION-DEPLOYMENT.md` — reviewed deployment contract;
- `SECURITY-MODEL.md` — security and zero-knowledge boundaries;
- `STABLE-EVIDENCE.md` — machine-readable Stable evidence contract;
- `UPSTREAM.md` — upstream synchronization and provenance expectations;
- `ROADMAP.md` — staged product direction;
- `REPOSITORY-STRUCTURE.md` — this document.

Repository documentation must not store reusable credentials, production secrets, private vault data, or sensitive recovery material.

### `migrations/`

Database schema migrations inherited from and maintained with the compatibility server.

Migration changes are release-critical and require migration, rollback, recovery, and compatibility review as appropriate.

### `scripts/`

GoreeVault-owned and inherited automation used for development, validation, security, compatibility, deployment, release, recovery, and evidence checks.

Release-blocking scripts should fail closed on missing or malformed required state. A script that only validates source should not silently mutate production state.

### `src/`

Rust server runtime and server-owned presentation.

This area includes authentication, authorization, persistence, configuration, API behavior, cryptographic integration, rate limiting, server-side templates, and GoreeVault-owned Admin/error presentation.

Internal `vaultwarden` names may remain when renaming them would unnecessarily increase protocol, database, build, or upstream-maintenance risk. User-facing GoreeVault-owned presentation must use GoreeVault identity and Glaze UI.

### `tests/`

Release-blocking regression and compatibility coverage.

Tests must use synthetic identities and data. Production databases, vault exports, credentials, backups, and private user content are prohibited test fixtures.

## Root files

### `README.md`

Public entry point for the GoreeVault repository. It must describe GoreeVault, not present the repository as upstream Vaultwarden, and must not recommend mutable production image tags.

### `GOREVAULT.md`

Maintained-fork product boundary, provenance, compatibility policy, security policy, and GoreeCloud-specific direction.

### `CONTRIBUTING.md`

Contributor expectations and validation requirements.

### `SECURITY.md`

Vulnerability reporting and security support boundary.

### `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, `build.rs`

Rust dependency, toolchain, and build inputs. Changes can alter runtime or supply-chain behavior and require corresponding validation.

### `DockerSettings.yaml`, `Dockerfile.j2`, generated Dockerfiles

Container-build generation inputs and outputs. Follow the generator comments and upstream-compatible workflow instead of editing generated outputs inconsistently.

## UI ownership boundary

GoreeVault-owned server UI belongs under the existing server static/template layout rather than a new top-level frontend tree.

A future GoreeVault Web client should use a separate application/repository boundary when implementation begins because it will have its own client-side cryptographic lifecycle, dependency graph, build pipeline, compatibility matrix, release lifecycle, and full Glaze UI ownership.

Until that client exists, the bundled upstream-compatible web vault is a temporary compatibility dependency. It is not a permanent Glaze UI exception and blocks product-wide Stable readiness under the current GoreeCloud baseline.

## Multi-user boundary

GoreeVault is a multi-user credential service, not an administrator-only single-user component.

Repository changes must preserve:

- individual user identities;
- private vault isolation;
- authorization checks on user-owned resources;
- organization and collection access boundaries;
- safe invitation/member lifecycle behavior;
- session/device revocation behavior;
- separation of network access from application authorization.

Multi-user regressions are release blockers.

## Adding a new component

Before adding a new top-level directory, repository, runtime service, client, or supporting component, document:

- Role and Purpose;
- ownership and maintenance boundary;
- security and privacy impact;
- data ownership and authoritative storage;
- authentication and authorization model;
- dependency and update model;
- backup/recovery impact;
- release/testing model;
- Glaze UI applicability for user-facing surfaces;
- migration and retirement path.

Prefer the simplest structure that keeps those boundaries clear and recoverable.
