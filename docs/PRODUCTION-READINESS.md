# GoreeVault Production Readiness

## Status model

GoreeVault uses evidence-based release states. A green source build is necessary but is not production authorization.

- **Development** — implementation work may change; no production use is authorized.
- **Release Candidate** — exact source and image artifacts have passed the automated release gates and are eligible for controlled validation.
- **Stable** — the exact RC artifact has also passed supported-client, operational, security, recovery, governance, and target-environment approval gates.

A release must not be promoted by version label alone.

## Release Candidate automated gates

The exact immutable candidate SHA must pass:

- GoreeVault CI, including PostgreSQL server and test-target compilation;
- source-format and template checks;
- GoreeVault Security Scan with zero unresolved HIGH/CRITICAL findings outside explicit, documented, expiring exceptions;
- workflow security analysis;
- black-box compatibility coverage for login, sync, CRUD, attachments, organizations/collections, TOTP, WebAuthn/passkey challenge/rejection, and refresh-token replay/concurrency behavior;
- destructive PostgreSQL plus `/data` backup/restore rehearsal;
- Vaultwarden baseline to GoreeVault migration and rollback rehearsal;
- non-publishing AMD64/ARM64 release-image build;
- production Compose policy validation;
- Glaze UI source-conformance validation for GoreeVault-owned browser surfaces.

Any code change after evidence is collected creates a new candidate SHA and requires new exact-head evidence.

## Stable governance gates

Before the first Stable release, verify all of the following in GitHub and record the result in release evidence:

- `main` is protected against unreviewed/direct release-source changes;
- required CI/status checks are enforced on `main`;
- CODEOWNERS review applies to runtime, workflow, security, dependency, deployment, migration, test, scanner-exception, and UI-conformance surfaces;
- a protected GitHub Actions `release` environment exists;
- the `release` environment requires at least one reviewer and prevents self-approval where GitHub supports it;
- default GitHub Actions token permissions are read-only;
- GitHub Dependabot vulnerability alerts are enabled;
- secret scanning and push protection are enabled where supported;
- private vulnerability reporting is enabled where supported;
- release publishing uses the protected environment and does not accept unreviewed branch builds;
- no standing temporary workflow retains unnecessary `contents: write` permission.

**Known repository-state blocker as of August 15, 2026:** the repository audit found no repository ruleset protecting `main` and no GitHub `release` environment. Stable promotion remains blocked until those controls are created and re-verified.

## Stable artifact gates

Stable must use the exact RC artifact that was tested. Record:

- source commit SHA;
- multi-architecture OCI manifest digest;
- PostgreSQL image digest and version;
- web-vault compatibility asset version/digest where applicable;
- Rust toolchain and lockfile state;
- release workflow run identifiers;
- security scan results and exception disposition state.

Do not rebuild a different image from the same source and treat it as equivalent evidence.

## Target-environment gates

Before production publication at `https://vault.goreecloud.com`:

- production Compose validation passes with the reviewed deployment files;
- the backend is loopback-only and is not directly publicly routed;
- TLS/WSS is provided by the trusted GoreeCloud reverse proxy;
- PostgreSQL is not host-published and remains on the internal backend network;
- the server is non-root, capability-free, read-only-root, and `no-new-privileges` is active;
- public registration is closed;
- `/admin` is disabled unless a separate reviewed administrative-access change authorizes it;
- a pre-deployment backup exists and its restore procedure has been rehearsed;
- storage capacity, certificate expiry, health, restart loops, and backup completion are monitored;
- production logs have been checked for secret/data minimization;
- rollback instructions and the previous known-good digests are recorded before deployment.

## Client gates

The real supported-client matrix must be exercised against the exact candidate. At minimum record the client name, platform, exact version/build, GoreeVault SHA/image digest, test time, and result for:

- sign-in and unlock;
- initial/full sync;
- create/update/delete;
- attachments;
- organization/collection behavior used by GoreeCloud;
- TOTP enrollment/use/recovery behavior;
- WebAuthn/passkey behavior on a real supported browser/device path;
- refresh-token rotation/replay behavior;
- logout and device/session invalidation behavior.

Synthetic API compatibility tests are strong release evidence but do not replace the real-client matrix.

## Glaze UI gates

Every GoreeVault-owned user-facing surface must conform to `docs/GLAZE-UI.md`. Material UI changes require authenticated browser review at representative desktop and mobile widths in System, Light, and Dark modes, including keyboard-only operation, reduced motion, increased contrast, forced colors where practical, error states, empty states, long values, and responsive tables/forms.

The bundled upstream-compatible web vault is currently a compatibility dependency rather than a GoreeVault-owned native surface. GoreeVault must not claim complete product-wide Glaze UI conformance until GoreeVault Web replaces or fully owns that presentation layer.

## Release decision

Stable promotion is denied if any of the following is true:

- a required workflow is failing, skipped unexpectedly, or ran against a different SHA;
- a fixed HIGH/CRITICAL vulnerability remains unresolved;
- a vulnerability exception is expired, broad, undocumented, or no longer justified;
- migration, rollback, backup/restore, or real-client evidence is missing;
- `main` or the release environment lacks the required governance controls;
- the production backend can be reached directly from the public network;
- image references are mutable;
- the release artifact differs from the tested artifact;
- UI conformance or accessibility review has a material unresolved defect;
- an upstream Vaultwarden security fix applicable to the candidate has not been evaluated.
