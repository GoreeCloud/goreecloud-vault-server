# GoreeCloud Vault Server Features

This file records current implemented behavior separately from planned or transitional capability.

## Implemented native foundation

### Native GoreeCloud-owned Rust boundary

`native/` is an independent Rust crate and the canonical long-term server implementation boundary. It is isolated from the inherited root Cargo workspace and currently uses only the Rust standard library.

### Fail-closed lifecycle status

The native crate records explicit production gates for GoreeCloud Identity, persistent storage, GoreeCloud Mesh, Glaze UI, Wardveil Security, Privacy Shield, Everkeep, real supported clients, WebAuthn/passkey acceptance, migration/rollback acceptance, repository/release governance, target-environment acceptance, and production approval.

All current production gates are false. The native `ready` command exits unsuccessfully until the required gates are accepted.

### Owner-scoped opaque encrypted-record development store

The native domain includes a memory-only store for already-protected record bytes.

Implemented behavior:

- bounded owner identifiers;
- bounded record identifiers;
- bounded non-empty encrypted payloads;
- positive record revisions;
- same record identifier permitted for different owners;
- owner-scoped get, list, and delete;
- deterministic record-ID ordering for owner lists;
- cross-owner lookup returns no other owner's record;
- debug output reports ciphertext length rather than ciphertext bytes.

The store does not encrypt, decrypt, parse, search, index, persist, synchronize, or transmit protected content.

### Dedicated native CI

The `GoreeCloud Vault Native Foundation` workflow verifies the isolated Cargo lock, formatting, strict Clippy lints, regression tests, locked build, bounded status output, and fail-closed readiness behavior on exact source revisions.

## Validated transitional compatibility capabilities

The inherited Vaultwarden-compatible path remains available as migration and compatibility reference material. Existing repository evidence includes compatibility coverage for authentication, sync, CRUD, attachments, organizations/collections, TOTP, WebAuthn-compatible paths, recovery, migration/rollback, security scanning, and release-image preflight.

These are not claims that equivalent native features are implemented.

## Not yet implemented in the native server

The following remain incomplete in the native path:

- production GoreeCloud Identity authentication;
- persistent PostgreSQL storage;
- network/HTTP API;
- token/session lifecycle;
- server-side authorization adapters beyond the in-memory owner domain;
- synchronization protocol;
- organizations and collection permissions;
- attachments;
- sends/sharing;
- passkey/WebAuthn server flows;
- TOTP flows;
- import/export and migration tooling;
- production deployment;
- Glaze UI server presentation;
- Wardveil Security integration;
- Privacy Shield integration;
- Everkeep integration;
- GoreeCloud Mesh integration;
- real-client acceptance;
- production approval;
- Stable release.

Planned capability is not considered implemented until its source and required acceptance evidence are integrated.
