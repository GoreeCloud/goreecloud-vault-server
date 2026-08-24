# GoreeCloud Vault Server Roadmap

This roadmap uses **GoreeCloud Vault Server** for the canonical server identity while preserving **GoreeVault** for the client family and historical product identity. See `SERVER-IDENTITY.md` for the authoritative naming boundary.

## v0.1.0 — Foundation

Established:

- Vaultwarden-derived server baseline with preserved AGPL/upstream provenance;
- GoreeCloud Vault Server product-facing server and administration identity;
- PostgreSQL target architecture;
- exact-head CI and security gates;
- zero-knowledge/client-side cryptographic boundary;
- upstream tracking strategy;
- development-only deployment baseline.

## v0.2.0 — Server compatibility, recovery, and hardening

v0.2 is the GoreeCloud Vault Server Release Candidate milestone. It proves the maintained server, compatibility, recovery, deployment, and release foundations. It does **not** by itself authorize product-wide Stable use because the primary browser vault remains an upstream compatibility dependency rather than a GoreeCloud-owned GoreeVault Web Glaze UI surface.

### Automated API, multi-user, and authentication gates

Established or under exact-head validation:

- fresh PostgreSQL startup and migrations;
- database-backed health checks;
- prelogin and closed-registration policy;
- isolated account creation/login;
- unrelated-user private-data isolation;
- organization/member and collection authorization transitions;
- single-use refresh-token rotation and replay rejection;
- atomic concurrent refresh-token consumption with exactly one winner;
- vault sync;
- personal cipher create/read/update/delete;
- attachment lifecycle;
- TOTP authentication/recovery coverage;
- WebAuthn challenge/rejection compatibility coverage.

### Recovery and migration gates

Established on the certified baseline and required on every release candidate:

- destructive PostgreSQL plus `/data` backup/restore rehearsal;
- exact Vaultwarden baseline to GoreeCloud Vault Server migration rehearsal;
- rollback rehearsal to the pre-migration state;
- non-publishing AMD64/ARM64 release-image build;
- source and built-image HIGH/CRITICAL security gates;
- hardened production Compose validation;
- repository-readiness and GoreeCloud-owned Glaze UI conformance checks;
- fail-closed exact-RC Stable evidence contract;
- read-only, secret-minimizing target-environment evidence collector with unit tests and explicit operator attestations for controls that cannot be proven from container metadata alone.

### Remaining v0.2 RC evidence

Before v0.2 can be treated as a supported server Release Candidate milestone:

- run and record the real supported Bitwarden client matrix on exact candidate artifacts;
- perform a real supported-browser/device WebAuthn/passkey flow;
- complete target-environment deployment rehearsal using the production contract and retain the generated target-environment evidence section;
- create/verify required GitHub governance controls from `docs/PRODUCTION-READINESS.md`;
- record completed RC-bound evidence for later Stable promotion.

Passing these items proves the server candidate. It does not override the product-wide Glaze UI gate.

## v0.3.0 — GoreeVault Web foundation

GoreeVault Web becomes the GoreeCloud-owned browser vault experience rather than a branded wrapper around the upstream-compatible web vault.

This milestone is required for the current product-wide Stable path because GoreeCloud requires Glaze UI on every controlled user-facing interface.

### Foundation contract established

`docs/WEB-CLIENT-CONTRACT.md` now defines the implementation boundary before a dedicated client repository is created. The contract establishes:

- Role and Purpose for the browser client;
- separation between GoreeVault Web and GoreeCloud Vault Server responsibilities;
- client-side zero-knowledge and cryptographic boundaries;
- multi-user account/session isolation requirements;
- browser storage and key-lifecycle rules;
- required compatible browser workflows before cutover;
- full Glaze UI and accessibility requirements;
- restrictive CSP and local-only presentation dependency direction;
- no analytics/behavioral tracking by default;
- immutable release, dependency, SBOM, migration, and rollback requirements;
- an explicit rule that creating a shell or repository does not close the Stable blocker by itself.

The dedicated GoreeVault Web repository/application remains to be created and implemented.

### Required implementation foundation

- dedicated GoreeCloud-native UI repository/application boundary;
- **Glaze UI Design Language** as the complete GoreeVault Web presentation and interaction system;
- local-only browser presentation dependencies under GoreeCloud Privacy by Default;
- accessible System/Light/Dark behavior, responsive layouts, keyboard/focus behavior, contrast and forced-colors support;
- individual multi-user account behavior and safe user/session boundaries;
- GoreeVault client SDK boundary;
- client-side vault encryption/decryption architecture using mature compatible cryptographic primitives;
- secure session locking and memory/key-lifecycle policy;
- import/export strategy;
- compatibility test coverage against GoreeCloud Vault Server;
- migration/fallback path from the bundled upstream web-vault dependency;
- browser accessibility and Glaze UI acceptance evidence.

The existing bundled upstream web vault remains a temporary compatibility asset until GoreeVault Web reaches the required compatibility and security gates. It is not a permanent production styling exception.

## v0.4.0 — GoreeVault Browser foundation

- Firefox and Chromium extension;
- Glaze UI adapted to browser-extension platform conventions;
- individual-user authentication/session lifecycle;
- URI matching and autofill;
- password/passphrase generator;
- capture/update credentials;
- secure local lock/unlock lifecycle;
- GoreeVault client SDK reuse;
- compatibility and threat-model review.

## v0.5.0 — GoreeVault Desktop foundation

- GoreeCloud-native desktop client;
- Glaze UI adapted to desktop accessibility and windowing conventions;
- individual-user authentication/session lifecycle;
- secure local encrypted state and lock lifecycle;
- browser/desktop handoff strategy where appropriate;
- update/distribution and code-signing plan.

## v0.6.0 — GoreeVault Mobile foundation

- Android-first GoreeVault mobile client, with iOS planning as applicable;
- Glaze UI adapted to native mobile conventions;
- individual-user authentication/session lifecycle;
- biometric/device-keystore integration using platform security APIs;
- autofill/credential-provider integration;
- secure background/lock behavior;
- mobile client compatibility matrix.

## v1.0.0 — Stable production release

Stable promotion requires the exact candidate artifact to satisfy `docs/PRODUCTION-READINESS.md`, including:

- proven multi-user identity, authorization, and private-data boundaries;
- compatibility and real-client evidence;
- security gates and reviewed exception state;
- migration and rollback;
- backup and verified restore;
- immutable multi-architecture release artifact;
- hardened production deployment validation;
- protected repository/release governance;
- target-environment operational evidence;
- product-wide Glaze UI conformance for every GoreeCloud-controlled user-facing surface;
- fail-closed validation of the RC-bound Stable evidence asset before the Stable and `latest` image tags are created.

Under the current approved path, GoreeVault Web must reach its security, compatibility, accessibility, and Glaze UI gates before v1.0 Stable promotion. A future formally approved material exception could alter that dependency only if it satisfies the GoreeCloud exception standard; no such exception is currently approved.

No semantic version or green build can bypass these gates.
