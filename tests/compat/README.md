# GoreeVault Compatibility Harness

This directory contains black-box integration tests for GoreeVault's Bitwarden-compatible server surface.

## Safety model

The harness never uses a production database, production data directory, real user email address, or real vault secret. PostgreSQL and `/data` use ephemeral `tmpfs` storage and are destroyed after each phase.

The test identity is `compat-user@example.invalid`, an intentionally non-deliverable address reserved for examples and testing.

## What is tested

The first v0.2 gate verifies:

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

Encrypted values are represented by obvious opaque test strings. The server is not expected to decrypt vault contents; client-side cryptography will receive its own dedicated compatibility fixtures in later gates.

## Run locally

Requirements:

- Docker Engine with Docker Compose v2
- Python 3

From the repository root:

```bash
bash scripts/compat.sh
```

The runner performs two isolated phases. It first starts GoreeVault with registration disabled and verifies rejection. It then destroys that environment, starts a fresh test instance with registration enabled, and runs authenticated API tests.

## Planned expansion

Additional v0.2 gates will cover organizations/collections, attachments, TOTP, WebAuthn/passkeys, import/export, backup/restore, and supported official-client compatibility.
