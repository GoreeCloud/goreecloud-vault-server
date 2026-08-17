# GoreeVault Repository Structure

## Purpose

This document defines the source-control structure of GoreeVault Server and the responsibility boundary of each major repository area.

The structure is intended to keep the maintained Vaultwarden compatibility core understandable while making GoreeCloud-owned security, deployment, release, Glaze UI, governance, evidence, and client-boundary work easy to locate and review.

## Structural principles

1. Keep compatibility-sensitive server code close to the upstream layout unless a different structure provides a clear security or maintenance benefit.
2. Keep GoreeCloud-owned validation, deployment, governance, evidence, and product documentation explicit rather than hiding it inside upstream files.
3. Do not create new top-level directories merely for visual organization; a directory should represent a durable ownership, build, runtime, or lifecycle boundary.
4. Keep reusable secrets and private production values outside the repository.
5. Keep generated files traceable to their generator/source inputs.
6. Keep release-blocking validators deterministic and dependency-light where practical.
7. Treat repository documentation as an implementation companion to authoritative GoreeCloud governance records, not as a replacement for those records.
8. Keep future client applications separated from the server when they own independent cryptographic, browser-storage, dependency, release, and UI lifecycles.

## Top-level layout

### `.github/`

Repository automation and review governance.

Includes:

- GitHub Actions workflows;
- CODEOWNERS;
- pull-request and issue configuration where applicable;
- release, security, compatibility, recovery, deployment, Glaze UI, evidence-tooling, and repository-readiness automation.

Changes here are security-sensitive because workflows may control release publication, registry access, evidence collection, or repository permissions.

### `deploy/`

GoreeCloud-owned production deployment contract.

This directory is separate from upstream development examples. Production deployment files must preserve immutable image references, private backend publication, database isolation, least privilege, backup/recovery requirements, and the canonical GoreeCloud service origin.

### `docker/`

Container build sources and generated image build definitions.

The repository retains upstream-compatible Docker generation where practical. Generated Dockerfiles must be changed through their documented source/generator path when the upstream build process requires it.

The root `Dockerfile` and generated Dockerfiles are build inputs, not production deployment manifests. Production runtime policy belongs in `deploy/`.

### `docs/`

GoreeVault implementation, architecture, security, compatibility, operational, release, client-boundary, and governance records.

Important documents include:

- `GLAZE-UI.md` — repository Glaze UI implementation contract;
- `WEB-CLIENT-CONTRACT.md` — future GoreeVault Web zero-knowledge, multi-user, storage, Glaze UI, accessibility, dependency, release, migration, and rollback boundary;
- `PRODUCTION-READINESS.md` — RC and Stable gates;
- `PRODUCTION-DEPLOYMENT.md` — reviewed deployment contract;
- `SECURITY-MODEL.md` — security and zero-knowledge boundaries;
- `STABLE-EVIDENCE.md` — machine-readable Stable evidence contract and target-environment collection process;
- `UPSTREAM.md` — upstream synchronization and provenance expectations;
- `ROADMAP.md` — staged product direction;
- `OPEN-READINESS-BLOCKERS.md` — unresolved exact-candidate gates;
- `REPOSITORY-STRUCTURE.md` — this document.

Repository documentation must not store reusable credentials, production secrets, private vault data, or sensitive recovery material.

### `migrations/`

Database schema migrations inherited from and maintained with the compatibility server.

Migration changes are release-critical and require migration, rollback, recovery, and compatibility review as appropriate.

### `scripts/`

GoreeVault-owned and inherited automation used for development, validation, security, compatibility, deployment, release, recovery, and evidence checks.

Release-blocking scripts should fail closed on missing or malformed required state. A script that only validates source should not silently mutate production state.

`scripts/collect-target-evidence.py` is explicitly read-only. It may inspect the reviewed production contract, restricted non-repository environment configuration, live Docker metadata, immutable image identity, and canonical HTTPS health, but it must not deploy, restart, stop, delete, back up, restore, or reconfigure production resources. It must not serialize secrets or full container environments.

### `src/`

Rust server runtime and server-owned presentation.

This area includes authentication, authorization, persistence, configuration, API behavior, cryptographic integration, rate limiting, server-side templates, and GoreeVault-owned Admin/error presentation.

Internal `vaultwarden` names may remain when renaming them would unnecessarily increase protocol, database, build, or upstream-maintenance risk. User-facing GoreeVault-owned presentation must use GoreeVault identity and Glaze UI.

### `tests/`

Release-blocking regression and compatibility coverage plus dependency-light tests for GoreeVault-owned validation/evidence tooling.

Tests must use synthetic identities and data. Production databases, vault exports, credentials, backups, and private user content are prohibited test fixtures.

`tests/test_collect_target_evidence.py` validates the target-evidence collector's fail-closed parsing and Docker-metadata decisions without a Docker daemon, target environment, production credentials, or private data.

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

A future GoreeVault Web client uses a separate application/repository boundary because it owns its own client-side cryptographic lifecycle, dependency graph, browser storage, build pipeline, compatibility matrix, release lifecycle, and full Glaze UI presentation. The server repository defines the implementation contract in `docs/WEB-CLIENT-CONTRACT.md`; that contract does not collapse the client into the server source tree.

Until that client exists and passes its required gates, the bundled upstream-compatible web vault is a temporary compatibility dependency. It is not a permanent Glaze UI exception and blocks product-wide Stable readiness under the current GoreeCloud baseline.

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
