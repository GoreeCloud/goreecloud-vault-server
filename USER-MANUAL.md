# GoreeCloud Vault Server User Manual

## Current status

GoreeCloud Vault Server is the canonical GoreeCloud server identity for the Vault service. GoreeVault remains a broader client-family and historical identity where compatibility requires it.

The server is under active pre-Stable development and acceptance work. Repository source, CI success, validation tooling, deployment scaffolding, or candidate evidence must not be interpreted as a production or Stable claim.

## Service boundary

The intended production service origin is:

```text
https://vault.goreecloud.com
```

The reviewed architecture keeps the application backend private behind the approved HTTPS/WSS publication path and requires PostgreSQL to remain internal. Exact production network, DNS, reverse-proxy, firewall, NetBird, database, and secret configuration must follow the accepted deployment records for the selected release candidate.

Do not copy placeholder values from `.env.template` into production without completing the deployment-specific secret and configuration process.

## Accounts and access

GoreeCloud Vault Server is designed for multi-user operation. Stable acceptance requires evidence for separate individual accounts, private-vault isolation, organization membership and collection authorization, permission changes, member removal, session/device invalidation, and operation without a shared administrator account.

Registration and administration policy are deployment controls. The Stable target requires registration closed and the application admin interface disabled unless a separately reviewed policy changes those requirements.

## Clients

Stable evidence currently requires real compatibility testing for these client kinds:

- web;
- Chromium extension;
- Firefox extension;
- desktop;
- Android;
- CLI.

Required acceptance includes sign-in/unlock, full sync, create/update/delete, attachments, organization collections, TOTP, refresh-token rotation/replay behavior, and logout/session invalidation.

A passing compatibility unit test is not a substitute for the real supported-client evidence required by Stable promotion.

## WebAuthn and passkeys

Stable acceptance requires retained real-browser WebAuthn evidence covering registration and authentication with the exact browser, browser version, platform, and authenticator used for the candidate.

The repository's validation harnesses and synthetic test paths do not by themselves authorize credential processing or Stable promotion.

## GoreeVault Web Argon2id work

The repository contains validation-only browser-target Argon2id WebAssembly work, deterministic artifact evidence, controlled HTTPS browser harnesses, and fail-closed browser-evidence validation.

These foundations remain separate from production credential processing until the exact generated browser artifacts, runtime registration, CSP/performance/memory/compatibility behavior, release inclusion, and final acceptance have all been reviewed for the selected candidate.

Never use synthetic test passwords, public test vectors, or validation-only private seeds as real credentials or device identities.

## Backup and recovery

Everkeep is the GoreeCloud continuity authority. Stable target-environment evidence requires a backup to be created, restore to be rehearsed, rollback to be recorded, and a distinct previous known-good immutable image to be identified.

A backup is not accepted merely because a file exists. The retained evidence must identify the backup and rollback records for the exact release candidate and target environment.

## Stable evidence workflow

Stable promotion is fail-closed. The canonical evidence validator is:

```text
scripts/validate-stable-evidence.py
```

The final evidence bundle binds the exact RC tag, source SHA, OCI manifest digest, PostgreSQL artifact, browser-vault asset, multi-user testing, real clients, WebAuthn, Glaze UI review, target-environment testing, repository governance, and final approvals.

### Evidence chronology

All component evidence timestamps must be at or before the bundle `collected_at` instant.

Final approvals are a true final review step: every approval timestamp must be at or after the latest non-approval evidence timestamp and at or before `collected_at`.

Timezone-aware timestamps are compared as absolute instants. Equivalent timestamps with different UTC offsets are valid. There is deliberately no arbitrary evidence-expiration interval in this rule; freshness policy must be introduced separately and explicitly if ever required.

An approval recorded before later multi-user, client, WebAuthn, Glaze UI, target-environment, or governance evidence is not final approval of that evidence and must be repeated after the later evidence exists.

## Mandatory GoreeCloud platform gates

Stable promotion also requires current validated application integration with:

- Glaze UI;
- Wardveil Security;
- Privacy Shield;
- Everkeep.

Repository CI, compatibility tests, deployment validation, encryption, or private networking cannot substitute for missing platform acceptance.

## Governance

Stable governance evidence is read-only collection of actual repository controls. The validator requires protected `main`, enforced required checks and CODEOWNERS review, a protected release environment, required release review with self-review prevention, read-only default Actions permissions, Dependabot alerts, and the defined conditional security-control states.

Evidence tooling does not enable these settings. If actual repository governance is not compliant, Stable remains blocked.

## Production boundaries

Do not treat any of the following as equivalent:

- source implemented;
- source tests pass;
- CI passes;
- candidate artifact exists;
- validation schema passes with synthetic fixtures;
- target deployment succeeds;
- production acceptance succeeds;
- Stable promotion is authorized.

Each state requires its own evidence and authority.

## Troubleshooting Stable evidence

If validation fails because a component timestamp is after `collected_at`, correct the evidence collection order or recollect the bundle. Do not edit timestamps merely to make validation pass.

If validation fails because an approval predates the latest non-approval evidence, obtain a new final approval after reviewing the complete evidence set.

If validation fails on a candidate identity, use the exact selected RC source SHA, tag, manifest digest, PostgreSQL artifact, and browser-vault asset. Do not reuse another artifact's digest to satisfy a field.

If a required platform or runtime acceptance record does not exist, the correct state is blocked/incomplete rather than a fabricated passing record.
