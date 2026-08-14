# GoreeVault Roadmap

## v0.1.0 — Foundation ✅

- Vaultwarden-derived server baseline
- GoreeVault product-facing server/admin identity
- PostgreSQL deployment
- GoreeVault CI checks
- security and architecture policy
- development-only deployment
- upstream tracking strategy

## v0.2.0 — Compatibility harness 🚧

### Gate A — Core API lifecycle ✅

- fresh PostgreSQL startup and migrations
- database-backed health check
- prelogin contract
- registration-closed policy test
- isolated account creation/login
- refresh-token rotation
- vault sync
- personal cipher create/read/update/delete

### Gate B — Collaboration and storage 🚧

Implemented in the current Gate B work:

- organization creation and owner access
- outsider authorization denial for organization resources
- collection creation/read/delete lifecycle
- outsider authorization denial for collection details
- organization-owned cipher creation and sync isolation
- attachment metadata/create/upload/read/delete lifecycle
- signed attachment download with byte-for-byte verification
- outsider authorization denial for cipher and attachment metadata

Still required to complete Gate B:

- member invitation/acceptance/confirmation lifecycle
- member role and collection ACL transitions
- import/export fixtures

### Gate C — Authentication regression

- TOTP enable/login/recovery tests
- WebAuthn/passkey regression tests
- trusted-device and 2FA-remember behavior

### Gate D — Recovery and supported clients

- PostgreSQL backup/restore automation
- data-directory backup/restore automation
- migration/rollback rehearsal
- supported Bitwarden CLI/browser/mobile compatibility matrix

v0.2 is complete only when the applicable gates are deterministic, isolated from production data, and repeatable in CI.

## v0.3.0 — GoreeVault Web foundation

- GoreeCloud-native UI repository
- client SDK boundary
- local vault encryption/decryption architecture
- session locking
- import/export strategy

## v0.4.0 — Browser extension foundation

- Firefox/Chromium extension
- URI matching
- autofill
- password generator
- capture/update credentials

## v1.0.0 — Production candidate

Production promotion only after migration, rollback, backup/restore, compatibility and security review gates are complete.
