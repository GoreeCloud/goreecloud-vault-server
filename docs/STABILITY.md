# GoreeVault Stability Policy

GoreeVault is being developed as a security-sensitive GoreeCloud service. A successful build is necessary, but it is not enough to call a release stable.

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

Release candidates must prove the authenticated lifecycle and recovery path.

Required in addition to Preview:

- isolated account creation and login fixture
- password refresh-token rotation and sequential replay rejection
- atomic refresh-token consumption under concurrent replay
- vault sync
- cipher create/read/update/delete
- organization and collection access-control tests
- attachment lifecycle tests
- TOTP and WebAuthn regression tests
- PostgreSQL backup and restore rehearsal
- `/data` backup and restore rehearsal
- migration and rollback rehearsal from the currently deployed GoreeCloud vault service
- supported Bitwarden client compatibility matrix
- security review of GoreeVault-specific code and deployment changes

### Stable / v1.0.0

A stable release must have no unresolved release-blocking failures in the Release Candidate gates. Production promotion must be reversible and must not require using production data as the first migration test.

## Stability invariants

The following are release-blocking requirements:

1. **Zero-knowledge compatibility is preserved.** GoreeVault must not introduce server-side plaintext vault decryption.
2. **Production data is never used for first-run migration testing.** Migration is rehearsed against a verified copy.
3. **Backups are verified by restoration.** Creating a backup file alone does not prove recoverability.
4. **Public registration is closed by default.** Any deployment that enables it is an explicit operator choice.
5. **The admin interface is disabled unless an Argon2 PHC `ADMIN_TOKEN` is deliberately configured.** Plaintext admin passwords are forbidden.
6. **PostgreSQL is not exposed to the public edge network.** Only the GoreeVault server may reach the database network in the standard deployment.
7. **Changes to cryptography, authentication, migrations, or authorization receive dedicated compatibility tests before production promotion.**
8. **Upstream provenance remains documented.** GoreeVault may change product identity without obscuring the Vaultwarden-derived implementation and license obligations.
9. **Refresh-token replay resistance is verified for both sequential and concurrent use.** A stable release must ensure a consumed password refresh token cannot be successfully reused, including during competing refresh requests.

## Current status

The v0.1.0 foundation established GoreeVault ownership, PostgreSQL deployment, CI, security documentation, and minimal product-facing branding.

The v0.2.0 stabilization track adds runtime PostgreSQL validation and begins the compatibility harness. Passing the v0.2 smoke suite promotes the project from build-only validation toward Preview maturity; it does **not** yet make GoreeVault a production replacement for the existing vault service.
