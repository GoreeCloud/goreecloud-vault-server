# GoreeCloud Vault Server

GoreeCloud Vault Server is GoreeCloud's self-hosted, zero-knowledge credential server. The long-term application is now being built as original GoreeCloud-owned native software under `native/`. The inherited Vaultwarden-compatible runtime remains in this repository as a **transitional compatibility, migration, and rollback baseline** while required behavior is replaced through independently reviewed native components.

> [!IMPORTANT]
> GoreeCloud Vault Server is under active development and stabilization. The current source line is **not approved for GoreeCloud Stable production use**. A successful native build, compatibility run, release preflight, or merged pull request does not authorize production deployment or Stable promotion.

## Canonical identity

The canonical server name is **GoreeCloud Vault Server** and the canonical repository is `GoreeCloud/goreecloud-vault-server`.

`GoreeVault` remains the broader client-family and historical project identity where explicitly documented. Current server-facing documentation, administration surfaces, release notes, and deployment records use **GoreeCloud Vault Server**. See `docs/SERVER-IDENTITY.md` and `docs/server-identity.json`.

## Native-first direction

The native implementation boundary is `native/`.

The current native foundation is intentionally small and security-first:

- an independent Rust crate isolated from the inherited root Cargo workspace;
- a fail-closed lifecycle/readiness model;
- an in-memory owner-scoped store for **opaque encrypted record bytes**;
- bounded identifiers and encrypted payload sizes;
- privacy-safe record debugging that does not print ciphertext;
- synthetic owner-isolation regression coverage;
- a dedicated exact-head GitHub Actions validation workflow;
- no telemetry, analytics, external integration, credential input, or network API.

The native foundation does **not** implement encryption, decryption, KDFs, authentication, production authorization, PostgreSQL persistence, sync, organizations, collections, attachments, passkeys/WebAuthn, browser UI, migration cutover, production deployment, or Stable approval.

Those capabilities must be added through separately reviewed native slices. Mature cryptographic and protocol primitives may be used as narrow foundations when reimplementation would materially increase security or interoperability risk, but inherited product architecture, UI, workflows, branding, and general application logic are not the native target.

## Transitional compatibility baseline

The existing Vaultwarden-derived Rust runtime, migrations, deployment tooling, compatibility harnesses, and migration/recovery evidence remain available while the native server is developed.

They currently provide important migration and compatibility evidence including:

- PostgreSQL startup and migrations;
- closed-registration behavior;
- isolated multi-user and organization/collection authorization checks;
- login, sync, cipher CRUD, attachments, TOTP, and WebAuthn-compatible behavior;
- refresh-token replay protection;
- destructive PostgreSQL plus `/data` recovery rehearsal;
- Vaultwarden-to-GoreeCloud migration and rollback rehearsal;
- source and image vulnerability gates;
- AMD64/ARM64 OCI release-image preflight;
- hardened production Compose validation;
- fail-closed Stable-evidence tooling.

This evidence does not make inherited product architecture the long-term GoreeCloud implementation, and it does not authorize a native cutover.

## Product role

GoreeCloud Vault Server is intended to provide secure multi-user credential, secret, secure-note, passkey, and encrypted-vault services while preserving client-side zero-knowledge boundaries.

The broader GoreeVault family remains separately lifecycle-managed:

- **GoreeCloud Vault Server** — this repository; native server implementation plus transitional compatibility/migration baseline;
- **GoreeVault Web** — GoreeCloud-owned browser-vault direction using Glaze UI;
- **GoreeVault Browser** — planned browser integration;
- **GoreeVault Desktop** — planned desktop client;
- **GoreeVault Mobile** — planned mobile client.

The server does not invent new cryptographic primitives merely to increase GoreeCloud-owned code. Encryption, KDF, token-signing, WebAuthn/passkey, and compatible protocol changes require security and interoperability evidence appropriate to their risk.

## Mandatory GoreeCloud platform gates

Stable qualification requires current, accepted evidence for every applicable GoreeCloud platform system. Repository CI cannot substitute for platform acceptance.

- **Glaze UI** — GoreeCloud-controlled user-facing interfaces must satisfy the current presentation, accessibility, adaptive-layout, appearance, and interaction contract.
- **Wardveil Security** — applicable protection, trust-state, diagnostics, security-policy, and evidence integration must be implemented and accepted.
- **Privacy Shield** — data minimization, sensitive-data handling, retention, privacy controls, and application adapters must be implemented and accepted.
- **Everkeep** — backup, restore, rollback, preservation, portability, continuity, and recovery obligations must be implemented and accepted.
- **GoreeCloud Identity** — production authentication must use a reviewed GoreeCloud Identity boundary; caller-controlled development identity is not production authentication.
- **GoreeCloud Mesh** — private networking is an additional network boundary where applicable and never substitutes for application authentication or authorization.

Missing, outdated, failed, or unverified required integration keeps the server non-Stable.

## Multi-user and zero-knowledge boundary

GoreeCloud Vault Server is a multi-user application.

Production readiness requires:

- individual user identities;
- private-vault isolation;
- application-level authorization on user-owned resources;
- organization and collection permission boundaries;
- reliable session/device invalidation and revocation;
- no shared administrator identity as a substitute for user identity;
- private networking that supplements rather than replaces authorization.

Protected vault contents are treated as opaque ciphertext where required by the zero-knowledge model. Production vault exports, passwords, credentials, private databases, recovery codes, reusable tokens, backups, and private user content are prohibited ordinary development fixtures.

## Security and privacy posture

Security-sensitive work is intentionally conservative.

- Do not invent or casually replace cryptographic primitives.
- Do not log passwords, access tokens, session cookies, private keys, decrypted vault content, or sensitive request bodies.
- Keep telemetry and analytics disabled unless separately required, reviewed, documented, and accepted.
- Keep external integrations disabled until they have an explicit role, data boundary, security review, and lifecycle owner.
- Do not expose the backend listener directly to the public internet.
- Use immutable production artifact identity.
- Keep public registration closed by default.
- Keep `/admin` disabled by default unless a separately restricted administrative path is approved.
- Keep reusable secrets outside source control and ordinary documentation.
- Require negative tests for cross-user access and fail-closed states.

See `SECURITY.md`, `docs/SECURITY-MODEL.md`, and `docs/PRODUCTION-DEPLOYMENT.md`.

## Repository structure

The repository now separates native product development from the transitional compatibility baseline:

```text
.github/       GitHub Actions, CODEOWNERS, release and security automation
native/        original GoreeCloud-owned Vault Server implementation
deploy/        reviewed transitional production deployment contract
docker/        transitional compatibility image build inputs
docs/          architecture, identity, readiness, migration and governance records
migrations/    transitional compatibility database migrations
scripts/       validation, evidence, migration, recovery and operational checks
src/           transitional Vaultwarden-compatible Rust runtime
tests/         compatibility and release-blocking regression/tooling coverage
web-client/    temporary GoreeVault Web incubation boundary
```

See `docs/REPOSITORY-STRUCTURE.md` before adding or moving a top-level component.

The required root product records are:

- `SPECIFICATIONS.md`
- `FEATURES.md`
- `BENEFITS.md`
- `COMPETITIVE-OBJECTIVES.md`
- `BRANDING.md`

These records distinguish implemented native behavior from planned or transitional capabilities.

## Native development validation

The dedicated native gate runs against exact pull-request revisions. The equivalent local checks are:

```bash
cargo generate-lockfile --manifest-path native/Cargo.toml
cargo fmt --manifest-path native/Cargo.toml -- --check
cargo clippy --locked --manifest-path native/Cargo.toml --all-targets -- -D warnings
cargo test --locked --manifest-path native/Cargo.toml
cargo build --locked --manifest-path native/Cargo.toml
cargo run --quiet --locked --manifest-path native/Cargo.toml -- status
cargo run --quiet --locked --manifest-path native/Cargo.toml -- ready
```

`ready` is expected to fail while production requirements remain incomplete.

Important transitional validators continue to include:

```bash
python3 scripts/validate-repository-readiness.py
python3 scripts/validate-glaze-ui.py
python3 scripts/validate-evidence-tooling.py
bash scripts/validate-production-deployment.sh
bash scripts/compat.sh
```

## Release and production boundary

GoreeCloud Vault Server follows exact-artifact, evidence-backed release governance.

Stable remains blocked until all applicable requirements are independently accepted, including:

- native feature and migration readiness;
- multi-user and authorization acceptance;
- Glaze UI, Wardveil Security, Privacy Shield, Everkeep, Identity, and Mesh requirements;
- real supported-client testing;
- real WebAuthn/passkey registration and authentication;
- destructive backup/restore and rollback proof;
- exact-candidate migration and rollback proof;
- target-environment rehearsal;
- repository and release governance;
- immutable release artifact evidence;
- final approvals after the evidence they approve.

No current source merge alone satisfies those requirements.

## Upstream provenance and transition

This repository began from **Vaultwarden** and retains required upstream attribution, licensing, compatibility reference material, and migration-sensitive structures during the native transition.

- Upstream project: **Vaultwarden**
- Upstream repository: `dani-garcia/vaultwarden`
- Recorded initial GoreeCloud baseline: `0cefa4cca7c9f2a5579dd290f78193b543818c51`
- License: **AGPL-3.0-only**

Required AGPL licensing, copyright notices, source-availability obligations, and appropriate upstream attribution remain in force. See `GOREVAULT.md` and `docs/UPSTREAM.md`.

GoreeCloud Vault Server is not affiliated with or endorsed by Bitwarden, Inc. Bitwarden is a trademark of its respective owner.

## Contributing and security reports

Read `CONTRIBUTING.md` before proposing changes. Authentication, authorization, cryptography, persistence, migration, recovery, release, deployment, evidence, and user-facing changes require review and evidence appropriate to their risk.

Do not publish exploit details in a public issue. Follow `SECURITY.md` for vulnerability reporting.
