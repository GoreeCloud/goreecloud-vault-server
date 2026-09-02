# GoreeCloud Vault Server Native Foundation

`native/` is the first original GoreeCloud-owned server implementation boundary for GoreeCloud Vault Server.

## Role and purpose

This crate establishes a buildable native Rust application core without inheriting Vaultwarden product architecture. The existing repository `src/`, migrations, compatibility harnesses, and deployment artifacts remain a transitional compatibility and migration baseline while native functionality is built and independently accepted.

The first foundation intentionally does only two application-level things:

1. models production readiness as explicit fail-closed gates; and
2. provides an in-memory owner-scoped store for **opaque encrypted record bytes**.

It does not implement HTTP, authentication, authorization tokens, database persistence, encryption, decryption, key derivation, WebAuthn, passkeys, synchronization, organizations, collections, attachments, sharing, browser UI, production deployment, or release approval.

## Security and privacy boundary

- Protected record bytes are opaque. Native code does not parse or decrypt them.
- Synthetic test data is used. Production vault exports, passwords, credentials, tokens, databases, backups, recovery codes, and private user content are prohibited fixtures.
- Record debug output reports only identifier, revision, and ciphertext length; it does not print ciphertext bytes.
- The development memory store is owner-scoped and permits the same record identifier for different owners without cross-owner lookup.
- There is no telemetry, analytics, network listener, credential input, or external integration in this foundation.
- Identifier and ciphertext inputs are bounded.
- The CLI reports only non-sensitive lifecycle gate state.
- Production readiness fails closed.

## Data ownership and persistence

The memory store is development-only and loses all records when the process ends. It is not an authoritative production store and is not a migration target.

A future persistent native store must receive a separate reviewed design covering owner isolation, PostgreSQL schema and migration behavior, backup and Everkeep recovery, retention, error handling, and rollback.

## Identity and authorization

There is no production GoreeCloud Identity adapter in this foundation. Owner identifiers exist only as synthetic domain inputs for isolation tests. Caller-controlled headers or CLI values are not accepted as production identity.

Network APIs must not be added until a reviewed authentication and authorization boundary exists.

## Dependencies

The native crate currently uses only the Rust standard library and the repository-pinned Rust toolchain. It is isolated from the inherited root Cargo workspace with its own empty `[workspace]` boundary.

Future third-party dependencies require explicit role, security, maintenance, update, and replacement review.

## Validation

The dedicated `GoreeCloud Vault Native Foundation` workflow verifies:

```bash
cargo generate-lockfile --manifest-path native/Cargo.toml
cargo fmt --manifest-path native/Cargo.toml -- --check
cargo clippy --locked --manifest-path native/Cargo.toml --all-targets -- -D warnings
cargo test --locked --manifest-path native/Cargo.toml
cargo build --locked --manifest-path native/Cargo.toml
cargo run --quiet --locked --manifest-path native/Cargo.toml -- status
cargo run --quiet --locked --manifest-path native/Cargo.toml -- ready
```

The final `ready` command is expected to return a non-success exit code while any production gate remains incomplete.

## Migration and retirement path

Vaultwarden-compatible source remains available for compatibility, migration, rollback, and behavioral reference during the transition. Native code must replace required behavior through reviewed GoreeCloud-owned components rather than copying inherited product architecture.

Retirement of inherited runtime code requires exact-candidate migration, rollback, real-client, recovery, platform-integration, and production acceptance evidence. This foundation does not authorize that retirement.
