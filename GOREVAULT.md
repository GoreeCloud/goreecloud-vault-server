# GoreeVault Server

GoreeVault is GoreeCloud's self-hosted, zero-knowledge credential platform.

## Product direction

This repository begins as a compatibility-focused derivative of Vaultwarden so GoreeCloud can establish a secure server, migration path, recovery model, deployment contract, and native product identity without inventing a new password-manager protocol or cryptographic system prematurely.

The long-term product is GoreeCloud-owned: GoreeVault Server plus GoreeVault Web, Browser, Desktop, and Mobile clients. Every GoreeVault-controlled user-facing interface uses the GoreeCloud Glaze UI Design Language.

## Mandatory GoreeCloud readiness gates

GoreeVault is intended for non-administrative users and is therefore a **multi-user application** under the GoreeCloud software baseline. Production readiness requires all three applicable platform gates:

1. **Multi-user readiness** — individual identities, private-data isolation, authorization boundaries, organization/collection controls, and session/device lifecycle behavior are proven.
2. **Security readiness** — authentication, authorization, zero-knowledge boundaries, secret handling, dependency review, secure network exposure, privacy-conscious logging, recovery, and security testing are proven.
3. **Glaze UI readiness** — every GoreeVault-controlled user-facing interface conforms to Glaze UI or an explicit material exception has been approved under the GoreeCloud exception standard.

No semantic version, successful build, compatibility test, or deployment rehearsal can bypass an applicable gate.

## Current compatibility boundary

The server keeps upstream-compatible cryptographic behavior, Bitwarden Client API behavior, database internals, migrations, and selected internal `vaultwarden` identifiers where those preserve compatibility and upstream maintainability.

GoreeVault-owned server presentation uses GoreeVault identity and Glaze UI. The bundled upstream-compatible web vault is a **temporary development and compatibility dependency** while GoreeVault Web is built. It is not treated as a permanent production exception merely because upstream styling is usable.

Under the current GoreeCloud baseline, product-wide Stable readiness remains blocked until the primary browser vault is GoreeVault-owned and Glaze-conformant, or a separately documented material exception is explicitly approved with its reason, impact, compensating controls, review condition, and removal condition. No such production exception is approved by this repository.

The implementation boundary for the future browser client is defined in `docs/WEB-CLIENT-CONTRACT.md`. That contract preserves the separate-client architecture, client-side zero-knowledge responsibility, multi-user isolation, browser-storage controls, Glaze UI requirements, accessibility, immutable release evidence, and reversible cutover requirements without claiming the client already exists.

## Upstream provenance

- Upstream project: Vaultwarden
- Upstream repository: `dani-garcia/vaultwarden`
- Initial GoreeVault baseline: `0cefa4cca7c9f2a5579dd290f78193b543818c51`
- License: AGPL-3.0-only

The original `LICENSE.txt`, copyright notices, attribution, and source-availability obligations must remain intact.

## Compatibility policy

Until GoreeVault owns and supports native clients, server changes must preserve compatibility with the approved Bitwarden client matrix. Compatibility-breaking changes require explicit architectural approval, migration/rollback planning, and client regression evidence.

The compatibility harness treats encrypted vault contents as opaque data because decryption is a client responsibility.

Compatibility is a security and migration constraint, not authority to preserve upstream presentation indefinitely.

## Security policy

Do not invent cryptographic primitives. Do not replace encryption, KDF, password hashing, WebAuthn/passkey, or token-signing behavior merely for branding or code ownership. Security-sensitive rewrites are separate reviewed projects with threat-model and regression updates.

Production clients use `https://vault.goreecloud.com`; TLS terminates at the trusted GoreeCloud reverse proxy and the HTTP backend must not be directly publicly exposed.

Tests must use synthetic identities and data. Production vault exports, databases, backups, reusable credentials, and private user information are prohibited test inputs.

Target-environment evidence collection is read-only and secret-minimizing. `scripts/collect-target-evidence.py` may inspect production container metadata and required policy values, but it must never serialize reusable credentials, full container environments, vault contents, session material, database passwords, recovery data, or other private values into Stable evidence.

## Repository structure

Repository ownership boundaries are documented in `docs/REPOSITORY-STRUCTURE.md`. New top-level components or client applications must have a durable Role and Purpose, security/data boundary, release lifecycle, recovery implications, and Glaze UI applicability before they are introduced.

## GoreeCloud standards

GoreeVault development follows the repository contracts in:

- `docs/GLAZE-UI.md` — GoreeCloud Glaze UI presentation/accessibility/privacy contract;
- `docs/WEB-CLIENT-CONTRACT.md` — GoreeVault Web zero-knowledge, multi-user, Glaze UI, accessibility, storage, release, migration, and rollback boundary;
- `docs/SECURITY-MODEL.md` and `SECURITY.md` — zero-knowledge and security boundaries;
- `docs/PRODUCTION-DEPLOYMENT.md` — hardened deployment contract;
- `docs/PRODUCTION-READINESS.md` — Release Candidate and Stable evidence/governance gates;
- `docs/STABLE-EVIDENCE.md` — exact-RC machine-readable Stable evidence contract and target-environment evidence collection;
- `docs/REPOSITORY-STRUCTURE.md` — source ownership and repository layout;
- `docs/UPSTREAM.md` — upstream tracking and review expectations.

A successful build or semantic version does not authorize production. Stable promotion requires the exact-artifact evidence, multi-user, security, Glaze UI, repository-governance, client, recovery, and target-environment gates defined by the readiness policy.
