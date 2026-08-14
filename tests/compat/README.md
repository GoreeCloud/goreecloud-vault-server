# GoreeVault Compatibility Harness

This directory contains black-box integration tests for GoreeVault's Bitwarden-compatible server surface.

## Safety model

The harness never uses a production database, production data directory, real user email address, or real vault secret. PostgreSQL and `/data` use ephemeral `tmpfs` storage and are destroyed after each phase.

The authenticated test phase uses two intentionally non-deliverable identities under `example.invalid`:

- `compat-owner@example.invalid`
- `compat-outsider@example.invalid`

All vault values and keys are obvious synthetic opaque strings.

## What is tested

### Gate A — Core API lifecycle

- fresh PostgreSQL startup and migrations
- DB-backed `/alive`
- prelogin contract
- closed-registration policy
- isolated account creation
- password grant login
- refresh-token rotation
- clean-account vault sync
- personal cipher create/read/update/delete
- sync consistency after update and delete

### Gate B — Collaboration and storage

- organization creation and owner access
- outsider denial for organization data
- initial and newly created collections
- outsider denial for collection details
- organization-owned cipher creation in a collection
- owner sync visibility and outsider sync isolation
- attachment metadata creation on an organization cipher
- outsider denial for attachment metadata
- multipart attachment upload
- signed attachment download with byte-for-byte verification
- attachment deletion and post-delete denial
- existing-account organization invitation in no-mail self-hosted mode
- accepted-but-unconfirmed member denial
- owner confirmation of an accepted member
- confirmed member collection/cipher visibility
- writable collection member cipher update
- read-only collection ACL denial
- restoration from read-only to writable access
- member removal and immediate loss of organization access
- personal import with folder/cipher relationship verification
- organization export containing expected collection and cipher
- outsider denial for organization export
- organization cipher and collection cleanup

Encrypted values are represented by opaque test strings. The server is not expected to decrypt vault contents; client-side cryptography will receive its own dedicated compatibility fixtures in later gates.

## Run locally

Requirements:

- Docker Engine with Docker Compose v2
- Python 3

From the repository root:

```bash
bash scripts/compat.sh
```

The runner performs two isolated server phases. It first starts GoreeVault with registration disabled and verifies rejection. It then destroys that environment, starts a fresh test instance with registration enabled, and runs authenticated API, authorization, import, and export tests.

On failure, the runner prints container status and recent GoreeVault/PostgreSQL logs before destroying the ephemeral environment.

The GitHub Actions workflow performs Python syntax, shell syntax, and Compose configuration validation before starting the expensive container build so harness mistakes fail quickly.

## Planned expansion

The next v0.2 gates cover TOTP, WebAuthn/passkeys, backup/restore, migration/rollback, and supported official-client compatibility.
