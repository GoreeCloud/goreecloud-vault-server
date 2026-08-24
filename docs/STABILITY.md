# GoreeCloud Vault Server Stability Policy

GoreeCloud Vault Server is a security-sensitive GoreeCloud service. A successful build is necessary, but it is not enough to call a release stable. Release maturity is determined by reproducible evidence across compatibility, authorization, authentication, recovery, migration, supply-chain, and real-client gates.

`GoreeVault` remains the broader client-family and historical product identity. This policy uses the canonical GoreeCloud Vault Server name for server maturity and release decisions.

## Release maturity

### Development

Development builds may change rapidly and are not approved for production vault data.

Required:

- Rust formatting and PostgreSQL compilation pass
- container image builds
- no tracked deployment secrets
- isolated development data only

### Preview

Preview builds must boot cleanly with PostgreSQL and pass the automated public API smoke suite.

Required in addition to Development:

- fresh PostgreSQL startup and migrations
- DB-backed `/alive` health check
- `/api/config` contract
- closed-registration policy validation
- prelogin contract validation
- unauthenticated vault access denial
- deterministic CI teardown with no retained test volumes

### Release candidate

Release candidates must prove the authenticated lifecycle, tenant isolation, recoverability, reversible migration, and release-artifact integrity.

Required in addition to Preview:

- isolated account creation and login fixture
- password refresh-token rotation and sequential replay rejection
- atomic refresh-token consumption under concurrent replay
- vault sync
- cipher create/read/update/delete
- organization and collection access-control tests, including cross-account isolation and restricted-member reassignment/removal
- attachment metadata, upload, byte-integrity download, and deletion tests
- TOTP enrollment, challenge, anti-replay, recovery-code, and post-recovery login tests
- automated WebAuthn challenge, RP-binding, malformed-attestation rejection, and no-credential-on-failure tests
- real-client WebAuthn/passkey registration and authentication with an actual authenticator before production promotion
- destructive PostgreSQL + `/data` backup/restore rehearsal with integrity verification
- migration and rollback rehearsal from the exact currently deployed or explicitly pinned upstream vault baseline
- supported Bitwarden client compatibility matrix
- GoreeCloud-owned multi-architecture container release pipeline
- immutable semantic-version and source-SHA image references
- SBOM and build provenance for the release image
- GitHub OIDC/Sigstore artifact attestation for the published image digest
- GoreeCloud Vault Server-owned vulnerability scanning that actually executes against both repository dependencies/source and the built production container image
- no unresolved fixed HIGH or CRITICAL vulnerability finding in either enforced vulnerability surface
- security review of GoreeCloud Vault Server-specific authentication, authorization, deployment, migration, and release changes

### Stable / v1.0.0

A stable release must have no unresolved release-blocking failures in the Release Candidate gates. Production promotion must be reversible and must not require using production data as the first migration test.

The Stable tag must point to the same tested source commit that passed the final RC gates. A different source commit requires a new RC cycle.

## Stability invariants

The following are release-blocking requirements:

1. **Zero-knowledge compatibility is preserved.** GoreeCloud Vault Server must not introduce server-side plaintext vault decryption.
2. **Production data is never used for first-run migration testing.** Migration is rehearsed against a verified copy or reproducible upstream fixture first.
3. **Backups are verified by restoration.** Creating a backup file alone does not prove recoverability.
4. **Public registration is closed by default.** Any deployment that enables it is an explicit operator choice.
5. **The admin interface is disabled unless an Argon2 PHC `ADMIN_TOKEN` is deliberately configured.** Plaintext admin passwords are forbidden.
6. **PostgreSQL is not exposed to the public edge network.** Only GoreeCloud Vault Server may reach the database network in the standard deployment.
7. **Changes to cryptography, authentication, migrations, or authorization receive dedicated compatibility tests before production promotion.**
8. **Upstream provenance remains documented.** GoreeCloud Vault Server may change product identity without obscuring the Vaultwarden-derived implementation and license obligations.
9. **Refresh-token replay resistance is verified for both sequential and concurrent use.** A consumed password refresh token must not be successfully reused, including during competing refresh requests.
10. **Organization boundaries are fail-closed.** A user must not gain collection access before membership confirmation, retain removed collection access after reassignment, or retain organization access after membership removal.
11. **Release artifacts are traceable to source.** Production images must be identifiable by immutable digest and source commit and carry verifiable provenance/attestation.
12. **Security checks must execute, not merely appear in the check list.** A skipped upstream-only scanner does not satisfy a GoreeCloud Vault Server release gate, and both source/dependency and built-image vulnerability scans must execute successfully.
13. **The tested rollback path remains available until production migration is accepted.** A release is not considered safely promoted if rollback was never rehearsed against the same storage contract.

## Required supported-client matrix

Before Stable, the candidate must be exercised against the supported Bitwarden-compatible client classes that GoreeCloud intends to use. Record the exact client version, platform, server release digest, date, and result for each run.

At minimum, validate:

- web vault login, sync, cipher CRUD, attachment access, TOTP, and organization collection access
- Chromium-family browser extension login/unlock, sync, autofill, create/update, and TOTP
- Firefox browser extension login/unlock, sync, autofill, create/update, and TOTP
- desktop client login/unlock, sync, create/update, attachments where supported, and TOTP
- Android client login/unlock, sync, autofill, create/update, attachments where supported, and TOTP
- CLI login, sync/list/get/create/edit where supported by the chosen client version
- at least one real WebAuthn/passkey registration and authentication path using a supported browser/client and actual authenticator

A client outside the declared supported matrix may be treated as unverified rather than silently assumed compatible.

## Release evidence

For each RC, record:

- source commit SHA and release tag
- published OCI manifest digest
- CI/compatibility/recovery/migration/security run references
- source/dependency and built-image vulnerability scan results
- restore rehearsal result
- migration and rollback result
- client matrix versions and results
- security review disposition
- known limitations accepted for that RC

Release evidence must describe what actually passed. Prepared tests or skipped checks are not counted as proof.

## Current status

The v0.1.0 foundation established GoreeCloud Vault Server ownership, PostgreSQL deployment, CI, security documentation, and minimal product-facing branding.

The v0.2.0 stabilization track is building the evidence required for Release Candidate maturity: runtime compatibility, tenant authorization, 2FA/passkey regression coverage, destructive recovery, reversible migration, GoreeCloud-owned release artifacts, executed source and built-image vulnerability scanning, and concurrent refresh-token replay resistance.

Until every Release Candidate gate above is satisfied, GoreeCloud Vault Server remains a stabilization/Preview candidate rather than a production replacement for the existing vault service.
