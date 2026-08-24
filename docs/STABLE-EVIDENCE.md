# GoreeCloud Vault Server Stable Release Evidence

Stable promotion must be backed by one machine-readable evidence record named `goreevault-stable-evidence.json` attached to the matching Release Candidate GitHub release.

The compatibility-era evidence filename is intentionally retained by current release tooling and does not define the canonical server identity. `GoreeVault` remains the broader client-family and historical product identity; the backend service is **GoreeCloud Vault Server**.

The evidence record is not a substitute for testing. It is the fail-closed handoff between completed manual/operational validation and the Stable promotion workflow.

## Why the evidence lives on the RC release

GoreeCloud Vault Server Stable must promote the exact source commit and exact multi-architecture OCI manifest that were tested as the Release Candidate. Committing evidence after RC testing would change the source SHA and invalidate that guarantee.

For that reason:

1. publish an RC only after automated RC gates pass;
2. test the exact RC artifact;
3. complete multi-user, real-client, WebAuthn, Glaze UI, target-environment, and governance validation;
4. prepare reviewed JSON section files from the canonical schema;
5. assemble and validate the canonical `goreevault-stable-evidence.json` against the exact RC identifiers;
6. attach the validated file to the matching RC GitHub release;
7. create the Stable tag only after repository governance and release-environment approval are complete.

The Stable release workflow downloads that exact asset from the selected RC release and rejects promotion when the file is missing, malformed, ambiguous, incomplete, contains unknown fields, references a different source SHA, references a different OCI manifest digest, or fails an applicable GoreeCloud production gate.

## Schema version 2

Schema version 2 adds explicit **multi-user readiness** and **product-wide Glaze UI readiness** evidence. These are mandatory because GoreeCloud Vault Server is intended for non-administrative users and GoreeCloud controls user-facing interfaces across the broader product family.

The validator intentionally does not treat the current upstream-compatible web vault as product-wide Glaze compliance. Stable evidence must represent the GoreeCloud-owned/approved production presentation state, not the transitional RC compatibility state.

The schema is strict. Unknown fields and duplicate JSON keys are rejected rather than ignored. This prevents ambiguous shadowed values and reduces the risk of accidentally storing unrelated or sensitive information in the release evidence file.

## Required artifact evidence

The record must contain:

- exact RC tag;
- exact 40-character source commit SHA;
- exact GoreeCloud Vault Server multi-architecture OCI manifest digest;
- PostgreSQL artifact as a syntactically valid immutable `name@sha256:<64-lowercase-hex>` reference;
- primary browser-vault asset as its own syntactically valid immutable `name@sha256:<64-lowercase-hex>` identity;
- exact deployed GoreeCloud Vault Server image reference whose digest equals the RC manifest digest;
- previous-known-good rollback artifact as a syntactically valid immutable reference distinct from the candidate server manifest;
- Central Time-aware or otherwise offset-aware collection/test timestamps.

The PostgreSQL and browser-vault digests must identify their own artifacts rather than reuse the GoreeCloud Vault Server manifest digest. A semantic version, mutable tag, filename without a checksum, or arbitrary string containing `@sha256:` is not accepted as immutable artifact evidence.

The browser asset identity can represent a release bundle, archive, container, or other reviewed browser artifact, but it must use the canonical `name@sha256:<digest>` evidence form so the release record identifies exact bytes rather than only a version label.

## Required multi-user evidence

The `multi_user` section must prove:

- individual accounts/identities are used;
- private vault data is isolated between unrelated users;
- unauthorized cross-user access is denied;
- organization membership boundaries are enforced;
- collection authorization is enforced;
- permission changes take effect;
- member removal takes effect;
- session/device invalidation works;
- ordinary users do not depend on a shared administrator account;
- the result is tied to a recorded evidence reference.

Synthetic compatibility coverage supports this gate but does not replace the exact-candidate evidence record.

## Required real-client evidence

The record must include real-client evidence for:

- web;
- Chromium extension;
- Firefox extension;
- desktop;
- Android;
- CLI.

Every required client must pass:

- sign-in and unlock;
- full sync;
- create/update/delete;
- attachments;
- organization/collection behavior;
- TOTP;
- refresh-token rotation/replay behavior;
- logout and device/session invalidation.

`docs/CLIENT-COMPATIBILITY.md` is the human-readable execution record for this matrix. Its six required client sections use the exact schema-version-2 check keys consumed by `scripts/validate-stable-evidence.py`. Under the current schema, a required `N/A`, `FAIL`, or `NOT TESTED` row cannot be translated to `true` in the final Stable evidence record.

## Required WebAuthn/passkey evidence

A real supported browser/device/authenticator path must prove both registration and authentication against the exact GoreeCloud Vault Server candidate. `docs/CLIENT-COMPATIBILITY.md` maps these to `webauthn.registration` and `webauthn.authentication` so the human evidence and machine record remain traceable.

## Required Glaze UI evidence

The `glaze_ui` section must prove product-wide readiness for every GoreeCloud-controlled user-facing interface, including:

- product-wide Glaze UI conformance;
- GoreeCloud ownership of the primary browser vault presentation;
- Glaze UI conformance of all controlled surfaces;
- System/Light/Dark behavior;
- keyboard accessibility and visible focus behavior;
- reduced-motion support;
- increased-contrast support;
- forced-colors/High Contrast operability;
- local-only presentation dependencies;
- absence of analytics/behavioral tracking in GoreeCloud-owned presentation;
- a recorded browser/accessibility evidence reference.

The current bundled upstream-compatible web vault is a temporary compatibility dependency. It does not satisfy `product_wide_conformance` or `primary_browser_vault_goreecloud_owned` and therefore cannot produce valid Stable evidence under the current approved path.

A future exception path must be explicitly designed and reviewed if GoreeCloud formally approves a material Glaze UI exception. No such exception is accepted by schema version 2.

## Target-environment evidence

The target rehearsal must verify the production contract at `https://vault.goreecloud.com`, including:

- backend listener is loopback-only;
- HTTPS/WSS terminates at the trusted GoreeCloud reverse proxy;
- PostgreSQL has no host-published port;
- the GoreeCloud Vault Server process runs non-root;
- the root filesystem is read-only;
- Linux capabilities are dropped;
- `no-new-privileges` is active;
- public registration is closed;
- `/admin` remains disabled under the current production policy;
- immutable image digests are used;
- a pre-deployment backup exists;
- restore has been rehearsed;
- rollback information is recorded;
- monitoring is verified;
- logs have been reviewed for sensitive-data minimization;
- the approved NetBird/private-access path is verified.

### Target evidence collector

`scripts/collect-target-evidence.py` provides a read-only helper for producing the exact `target_environment` object after a real target-environment rehearsal.

The collector intentionally does **not** create a complete Stable evidence record and cannot attest client, WebAuthn, Glaze UI, governance, or reviewer approval on the operator's behalf. Its scope is limited to the target-environment section.

Machine-observed checks include:

- the reviewed production deployment source validator still passes;
- the production Compose model renders with the operator-controlled environment file;
- the production environment file is not group/world accessible;
- configured and live GoreeCloud Vault Server/PostgreSQL images are immutable digest references;
- the live GoreeCloud Vault Server image matches the expected RC manifest digest;
- both GoreeCloud Vault Server and PostgreSQL containers are running and healthy;
- the server uses the reviewed non-zero numeric UID/GID runtime form;
- the backend is published only on `127.0.0.1`;
- PostgreSQL has no host-published port;
- the root filesystem is read-only;
- all Linux capabilities are dropped;
- `no-new-privileges` is active;
- registration is closed;
- the admin token is absent/empty under the current disabled-admin policy;
- the canonical HTTPS `/alive` endpoint responds successfully.

Controls that cannot be proven safely from container metadata require explicit operator flags, including real HTTPS/WSS reverse-proxy validation, backup creation, restore rehearsal, rollback recording, monitoring verification, privacy-conscious log review, and the approved NetBird/private administrative path.

The collector never serializes container environment values, database credentials, vault contents, session material, tokens, or other reusable secrets. It reads only the values required to decide whether a control passes and emits the non-secret Stable evidence fields. When written to a file, the collector applies mode `0600`.

Example after a real rehearsal:

```bash
python3 scripts/collect-target-evidence.py \
  --env-file /etc/goreevault/production.env \
  --expected-manifest-digest "sha256:<64-hex RC manifest digest>" \
  --previous-known-good-image "ghcr.io/goreecloud/goreecloud-vault-server@sha256:<64-hex previous digest>" \
  --backup-reference "<approved backup or snapshot reference>" \
  --rollback-reference "<rollback rehearsal/runbook reference>" \
  --reverse-proxy-https-wss \
  --backup-created \
  --restore-rehearsed \
  --rollback-recorded \
  --monitoring-verified \
  --logs-reviewed-for-sensitive-data \
  --netbird-path-verified \
  --output target-environment.json
```

The `/etc/goreevault` path is a compatibility-era operational identifier intentionally retained by the current deployment contract; it does not define the current product name.

The default evidence timestamp uses `America/Chicago`, matching GoreeCloud's Central Time documentation convention. The resulting `target-environment.json` is the value for the full Stable record's `target_environment` field; it must still be reviewed before insertion and final validation.

Do not run the collector against production merely to obtain a passing JSON file. Run it only after the underlying backup, restore, rollback, monitoring, log, network, and client work has actually been performed.

## Governance evidence

Stable evidence must record the required repository controls as verified:

- protected `main`;
- required checks;
- CODEOWNERS review enforcement;
- protected `release` environment;
- required release reviewer;
- self-review prevention;
- read-only default GitHub Actions token permissions;
- Dependabot vulnerability alerts.

Secret scanning, push protection, and private vulnerability reporting must be recorded as `pass` or `not_supported`. `not_supported` is acceptable only when the GitHub repository/account capability is genuinely unavailable, not as a waiver.

## Human-readable RC evidence index

`docs/RC-EVIDENCE.md` is the human-readable evidence index for the candidate. It tracks automated exact-head gates, supply chain, recovery/migration, security disposition, multi-user proof, the real-client/WebAuthn matrix, target rehearsal, server and product-wide Glaze UI state, open blockers, RC qualification, Stable assembly, and post-promotion verification.

Approval of the server RC section does not imply product-wide Stable approval. The final Stable workflow relies on the validated machine-readable evidence asset.

## Strict Stable evidence assembly

`scripts/assemble-stable-evidence.py` is the preferred final assembly path. It reduces hand-edit risk by combining separately reviewed JSON sections and invoking the same Stable validator before writing the canonical file.

The assembler requires these section files:

- `rc.json` — the `rc` object;
- `multi-user.json` — the `multi_user` object;
- `clients.json` — the six-client array;
- `webauthn.json` — the `webauthn` object;
- `glaze-ui.json` — the `glaze_ui` object;
- `target-environment.json` — the `target_environment` object, normally produced/reviewed from the target collector after the real rehearsal;
- `governance.json` — the `governance` object;
- `approvals.json` — the reviewer-approval array.

The section files must contain only their exact schema value, not a wrapper such as `{ "rc": ... }`. They are release evidence and must not contain passwords, tokens, cookies, decrypted vault values, private keys, TOTP seeds, recovery codes, database credentials, or unrelated private data.

Example:

```bash
python3 scripts/assemble-stable-evidence.py \
  --rc rc.json \
  --multi-user multi-user.json \
  --clients clients.json \
  --webauthn webauthn.json \
  --glaze-ui glaze-ui.json \
  --target-environment target-environment.json \
  --governance governance.json \
  --approvals approvals.json \
  --expected-source-sha "<40-character RC source SHA>" \
  --expected-rc-tag "v0.3.0-rc.1" \
  --expected-manifest-digest "sha256:<64-hex RC manifest digest>" \
  --output goreevault-stable-evidence.json
```

The assembler:

- parses every section using duplicate-key rejection;
- assembles only the known schema-version-2 top-level fields;
- does not offer a placeholder-acceptance mode;
- validates the complete record against the exact expected source SHA, RC tag, and server manifest digest;
- refuses an existing output unless `--force` is explicitly supplied;
- refuses to write through a symbolic-link output path;
- writes the validated file with mode `0600` and flushes it before reporting success;
- does not create evidence, execute missing tests, or mark a release gate complete.

`--force` only permits replacing an ordinary existing output file after the newly assembled record has passed validation. It does not relax schema or release checks.

## Independent local validation

After assembly, run the validator independently using the same exact RC values:

```bash
python3 scripts/validate-stable-evidence.py \
  goreevault-stable-evidence.json \
  --expected-source-sha "<40-character RC source SHA>" \
  --expected-rc-tag "v0.3.0-rc.1" \
  --expected-manifest-digest "sha256:<64-hex manifest digest>"
```

The validator uses only the Python standard library and fails closed. It rejects placeholders, missing or unknown fields, duplicate JSON keys, malformed immutable references, incomplete client/multi-user/Glaze/target/governance evidence, and mismatched exact-RC identifiers.

## Upload to the matching RC release

After local validation, attach the file to the matching RC GitHub release using an approved administrative workflow. One supported CLI form is:

```bash
gh release upload v0.3.0-rc.1 \
  goreevault-stable-evidence.json \
  --clobber
```

Do not upload evidence to a different RC release, rename the canonical asset, or reuse evidence from another source SHA or manifest digest.

## Stable promotion behavior

On a Stable tag, `.github/workflows/goreevault-release.yml`:

1. locates the latest matching RC tag;
2. verifies the Stable tag points to the same source commit;
3. resolves the exact RC OCI manifest digest;
4. downloads `goreevault-stable-evidence.json` from that RC release;
5. validates the evidence against the selected RC tag, source SHA, manifest, immutable supporting artifacts, multi-user gate, product-wide Glaze UI gate, real-client matrix, WebAuthn, target environment, governance, and approvals;
6. only then promotes the exact RC manifest to the Stable version and `latest`.

The workflow filename is a compatibility-era internal identifier. A missing or invalid evidence asset blocks Stable publication.
