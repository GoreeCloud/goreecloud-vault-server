# GoreeVault Roadmap

## v0.1.0 — Foundation

Established:

- Vaultwarden-derived server baseline with preserved AGPL/upstream provenance;
- GoreeVault product-facing server and administration identity;
- PostgreSQL target architecture;
- exact-head CI and security gates;
- zero-knowledge/client-side cryptographic boundary;
- upstream tracking strategy;
- development-only deployment baseline.

## v0.2.0 — Compatibility, recovery, and hardening

### Automated API and authentication gates

Established or under exact-head validation:

- fresh PostgreSQL startup and migrations;
- database-backed health checks;
- prelogin and closed-registration policy;
- isolated account creation/login;
- single-use refresh-token rotation and replay rejection;
- atomic concurrent refresh-token consumption with exactly one winner;
- vault sync;
- personal cipher create/read/update/delete;
- organization/member and collection access-control behavior;
- attachment lifecycle;
- TOTP authentication/recovery coverage;
- WebAuthn challenge/rejection compatibility coverage.

### Recovery and migration gates

Established on the certified baseline and required on every release candidate:

- destructive PostgreSQL plus `/data` backup/restore rehearsal;
- exact Vaultwarden baseline to GoreeVault migration rehearsal;
- rollback rehearsal to the pre-migration state;
- non-publishing AMD64/ARM64 release-image build;
- source and built-image HIGH/CRITICAL security gates.

### Remaining v0.2 release evidence

Before v0.2 can be treated as a supported release milestone:

- run and record the real supported Bitwarden client matrix on exact candidate artifacts;
- perform a real supported-browser/device WebAuthn/passkey flow;
- complete target-environment deployment rehearsal using the production contract;
- create/verify required GitHub governance controls from `docs/PRODUCTION-READINESS.md`;
- record those completed gates in the validated `goreevault-stable-evidence.json` attached to the exact matching RC release before Stable promotion.

## v0.3.0 — GoreeVault Web foundation

GoreeVault Web becomes the GoreeCloud-owned browser vault experience rather than a branded wrapper around the upstream-compatible web vault.

Required foundation:

- dedicated GoreeCloud-native UI repository/application boundary;
- **Glaze UI Design Language** as the complete GoreeVault Web presentation and interaction system;
- local-only browser presentation dependencies under GoreeCloud Privacy by Default;
- accessible System/Light/Dark behavior, responsive layouts, keyboard/focus behavior, contrast and forced-colors support;
- GoreeVault client SDK boundary;
- client-side vault encryption/decryption architecture using mature compatible cryptographic primitives;
- secure session locking and memory/key-lifecycle policy;
- import/export strategy;
- compatibility test coverage against the GoreeVault server.

The existing bundled upstream web vault remains a transitional compatibility asset until GoreeVault Web reaches the required compatibility and security gates. Product-wide Glaze UI conformance is not claimed before that transition.

## v0.4.0 — GoreeVault Browser foundation

- Firefox and Chromium extension;
- Glaze UI adapted to browser-extension platform conventions;
- URI matching and autofill;
- password/passphrase generator;
- capture/update credentials;
- secure local lock/unlock lifecycle;
- GoreeVault client SDK reuse;
- compatibility and threat-model review.

## v0.5.0 — GoreeVault Desktop foundation

- GoreeCloud-native desktop client;
- Glaze UI adapted to desktop accessibility and windowing conventions;
- secure local encrypted state and lock lifecycle;
- browser/desktop handoff strategy where appropriate;
- update/distribution and code-signing plan.

## v0.6.0 — GoreeVault Mobile foundation

- Android-first GoreeVault mobile client, with iOS planning as applicable;
- Glaze UI adapted to native mobile conventions;
- biometric/device-keystore integration using platform security APIs;
- autofill/credential-provider integration;
- secure background/lock behavior;
- mobile client compatibility matrix.

## v1.0.0 — Stable production release

Stable promotion requires the exact candidate artifact to satisfy `docs/PRODUCTION-READINESS.md`, including:

- compatibility and real-client evidence;
- security gates and reviewed exception state;
- migration and rollback;
- backup and verified restore;
- immutable multi-architecture release artifact;
- hardened production deployment validation;
- protected repository/release governance;
- target-environment operational evidence;
- Glaze UI conformance for every GoreeVault-owned surface;
- fail-closed validation of the RC-bound Stable evidence asset before the Stable and `latest` image tags are created.

No semantic version or green build can bypass those gates.
