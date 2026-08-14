# GoreeVault Compatibility Harness

This directory contains black-box integration tests for GoreeVault's Bitwarden-compatible server surface.

## Safety model

The harness never uses a production database, production data directory, real user email address, or real vault secret. PostgreSQL and `/data` use ephemeral `tmpfs` storage and are destroyed after each phase.

The authenticated test phase uses two intentionally non-deliverable identities under `example.invalid`:

- `compat-owner@example.invalid`
- `compat-outsider@example.invalid`

All vault values and keys are obvious synthetic opaque strings.

## What is tested

The current v0.2 harness verifies:

1. fresh PostgreSQL startup and migrations
2. DB-backed `/alive`
3. prelogin contract
4. public registration remains rejected when `SIGNUPS_ALLOWED=false`
5. isolated account creation when test-only signups are enabled
6. password grant login
7. refresh-token rotation
8. clean-account vault sync
9. personal cipher create/read/update/delete
10. sync consistency after update and delete
11. organization creation and owner access
12. outsider denial for organization data
13. initial and newly created collections
14. outsider denial for collection details
15. organization-owned cipher creation in a collection
16. owner sync visibility and outsider sync isolation for organization data
17. attachment metadata creation on an organization cipher
18. outsider denial for attachment metadata
19. multipart attachment upload
20. signed attachment download with byte-for-byte verification
21. attachment deletion and post-delete denial
22. existing-account organization invitation in no-mail self-hosted mode
23. accepted-but-unconfirmed member denial
24. owner confirmation of an accepted member
25. confirmed member collection/cipher visibility
26. writable collection member cipher update
27. read-only collection ACL denial
28. restoration from read-only to writable access
29. member removal and immediate loss of organization access
30. organization cipher and collection cleanup

Encrypted values are represented by opaque test strings. The server is not expected to decrypt vault contents; client-side cryptography will receive its own dedicated compatibility fixtures in later gates.

## Run locally

Requirements:

- Docker Engine with Docker Compose v2
- Python 3

From the repository root:

```bash
bash scripts/compat.sh
```

The runner performs two isolated phases. It first starts GoreeVault with registration disabled and verifies rejection. It then destroys that environment, starts a fresh test instance with registration enabled, and runs authenticated API and authorization tests.

On failure, the runner prints container status and recent GoreeVault/PostgreSQL logs before destroying the ephemeral environment.

The GitHub Actions workflow performs Python syntax, shell syntax, and Compose configuration validation before starting the expensive container build so harness mistakes fail quickly.

## Planned expansion

Additional v0.2 gates will cover import/export, TOTP, WebAuthn/passkeys, backup/restore, migration/rollback, and supported official-client compatibility.
