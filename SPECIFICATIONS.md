# GoreeCloud Vault Server Specifications

## Status

Active native development. Not approved for Stable production use.

## Role and purpose

GoreeCloud Vault Server is the server component for GoreeCloud credential, secret, secure-note, passkey, and encrypted-vault services. The long-term implementation is original GoreeCloud-owned native software.

The inherited Vaultwarden-compatible runtime is transitional compatibility, migration, rollback, and behavioral-reference material. It is not the native product architecture target.

## Current native implementation

The implemented native foundation under `native/` currently provides:

- an isolated Rust 2024 crate using the repository-pinned Rust toolchain;
- no third-party runtime dependencies;
- an explicit fail-closed production-readiness gate model;
- a development-only in-memory encrypted-record store;
- owner-scoped record creation, lookup, list, and deletion behavior inside the native domain;
- opaque ciphertext handling with no encryption, decryption, parsing, indexing, or content logging;
- bounded owner identifiers, record identifiers, ciphertext payloads, and positive record revisions;
- synthetic regression coverage for cross-owner isolation, bounded inputs, deterministic owner-scoped listing, deletion isolation, and ciphertext-safe debug output;
- a bounded CLI status surface with no network listener or credential input;
- dedicated exact-head native CI.

## Native security model

The native server must preserve a zero-knowledge boundary appropriate to the supported client model.

Protected vault content must remain opaque to server code where the protocol requires client-side encryption. Native server logic must not add plaintext storage or server-side decryption merely to simplify implementation.

The native application must not invent cryptographic primitives. Mature and independently reviewed cryptographic, KDF, WebAuthn/passkey, protocol, codec, runtime, or database foundations may be used narrowly when reimplementation would materially increase security or interoperability risk.

## Multi-user and authorization requirements

Native behavior must be multi-user from the beginning.

Required properties include:

- stable authenticated user identity;
- fail-closed missing or invalid identity;
- owner-scoped private record access;
- organization and collection authorization;
- session/device lifecycle and revocation;
- cross-user negative testing;
- application authorization independent of private-network reachability.

The current native foundation uses synthetic owner identifiers only for domain-isolation tests. It does not implement production authentication.

## Data and persistence

Current native record storage is memory-only development state.

A future production store must:

- use an approved persistent database boundary;
- preserve owner isolation in storage queries and uniqueness rules;
- store only protocol-required server-visible data;
- treat protected record payloads as opaque;
- support safe schema evolution;
- support Everkeep backup, restore, rollback, continuity, and destructive recovery rehearsal;
- avoid reusable secrets in source, logs, fixtures, or ordinary documentation;
- provide bounded privacy-safe errors.

No native production schema or data migration exists yet.

## APIs and networking

The current native foundation has no network listener and no HTTP/API surface.

A future network API requires separate review for:

- GoreeCloud Identity authentication;
- authorization on every private resource;
- bounded request/response bodies;
- method and content-type handling;
- rate limiting and abuse controls;
- privacy-safe errors and logs;
- reverse-proxy trust;
- GoreeCloud Mesh applicability;
- TLS and internal transport assumptions;
- negative cross-user tests.

The backend must not be published directly to the public internet.

## Platform integration

Stable requires current accepted integration with all applicable GoreeCloud platform systems:

- Glaze UI
- Wardveil Security
- Privacy Shield
- Everkeep
- GoreeCloud Identity
- GoreeCloud Mesh

Platform integration must be substantive. Naming or importing a shared package without implementing the required behavior and acceptance does not satisfy the gate.

## Compatibility and migration

The repository retains a Vaultwarden-compatible runtime and compatibility test harness during the native transition.

Native replacement must be demonstrated against exact supported workflows before inherited runtime retirement. Migration acceptance must prove authentication, synchronization, authorized data access, organization/collection behavior, attachments and required second-factor flows without private-data leakage or corruption.

Rollback must preserve a safe path to the previously accepted service state. A successful process start or schema migration is not migration acceptance.

## Recovery

Production acceptance requires complete backup coverage for every required persistent component and an isolated destructive restore rehearsal. Recovery must not depend on undocumented local state or a single surviving production host.

## User interface

Server-owned user-facing surfaces must use current Glaze UI requirements. The primary browser vault is a separate GoreeVault client lifecycle and must become GoreeCloud-owned and Glaze-conformant before product-wide Stable qualification unless a separately documented material exception is explicitly approved.

The current native server foundation has no user-facing UI.

## Release lifecycle

Source validation, release acceptance, and production acceptance are separate.

Stable requires exact-artifact evidence for applicable gates, including:

- native implementation acceptance;
- multi-user security;
- real supported clients;
- real WebAuthn/passkey flows;
- Glaze UI, Wardveil Security, Privacy Shield, Everkeep, Identity, and Mesh;
- backup and destructive restore;
- migration and rollback;
- target-environment rehearsal;
- repository/release governance;
- immutable source/tag/image identities;
- final approvals after the evidence being approved.

The native foundation does not satisfy these gates by itself.

## Non-goals

The project does not:

- create new cryptography for branding;
- store plaintext protected vault content on the server;
- treat private networking as user authorization;
- preserve inherited application architecture merely because it exists;
- claim production readiness from green CI;
- use mutable release identities for production;
- use production secrets or private user data as ordinary development fixtures.
