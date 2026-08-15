# GoreeVault Stable Release Evidence

Stable promotion must be backed by one machine-readable evidence record named `goreevault-stable-evidence.json` attached to the matching Release Candidate GitHub release.

The evidence record is not a substitute for testing. It is the fail-closed handoff between completed manual/operational validation and the Stable promotion workflow.

## Why the evidence lives on the RC release

GoreeVault Stable must promote the exact source commit and exact multi-architecture OCI manifest that were tested as the Release Candidate. Committing evidence after RC testing would change the source SHA and invalidate that guarantee.

For that reason:

1. publish an RC only after automated RC gates pass;
2. test the exact RC artifact;
3. complete multi-user, real-client, WebAuthn, Glaze UI, target-environment, and governance validation;
4. create `goreevault-stable-evidence.json` from `docs/stable-evidence.example.json`;
5. validate it locally with `scripts/validate-stable-evidence.py`;
6. attach the validated file to the matching RC GitHub release;
7. create the Stable tag only after repository governance and release-environment approval are complete.

The Stable release workflow downloads that exact asset from the selected RC release and rejects promotion when the file is missing, malformed, incomplete, references a different source SHA, references a different OCI manifest digest, or fails an applicable GoreeCloud production gate.

## Schema version 2

Schema version 2 adds explicit **multi-user readiness** and **product-wide Glaze UI readiness** evidence. These are mandatory because GoreeVault is intended for non-administrative users and has controlled user-facing interfaces.

The validator intentionally does not treat the current upstream-compatible web vault as product-wide Glaze compliance. Stable evidence must represent the GoreeVault-owned/approved production presentation state, not the transitional RC compatibility state.

## Required artifact evidence

The record must contain:

- exact RC tag;
- exact 40-character source commit SHA;
- exact GoreeVault multi-architecture OCI manifest digest;
- digest-pinned PostgreSQL image reference;
- exact browser-vault asset/client identification;
- Central Time-aware or otherwise offset-aware collection/test timestamps.

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

## Required WebAuthn/passkey evidence

A real supported browser/device/authenticator path must prove both registration and authentication against the exact candidate.

## Required Glaze UI evidence

The `glaze_ui` section must prove product-wide readiness for every GoreeVault-controlled user-facing interface, including:

- product-wide Glaze UI conformance;
- GoreeCloud ownership of the primary browser vault presentation;
- Glaze UI conformance of all controlled surfaces;
- System/Light/Dark behavior;
- keyboard accessibility and visible focus behavior;
- reduced-motion support;
- increased-contrast support;
- forced-colors/High Contrast operability;
- local-only presentation dependencies;
- absence of analytics/behavioral tracking in GoreeVault-owned presentation;
- a recorded browser/accessibility evidence reference.

The current bundled upstream-compatible web vault is a temporary compatibility dependency. It does not satisfy `product_wide_conformance` or `primary_browser_vault_goreecloud_owned` and therefore cannot produce valid Stable evidence under the current approved path.

A future exception path must be explicitly designed and reviewed if GoreeCloud formally approves a material Glaze UI exception. No such exception is accepted by schema version 2.

## Target-environment evidence

The target rehearsal must verify the production contract at `https://vault.goreecloud.com`, including:

- backend listener is loopback-only;
- HTTPS/WSS terminates at the trusted GoreeCloud reverse proxy;
- PostgreSQL has no host-published port;
- the GoreeVault server runs non-root;
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

## Local validation

Use the exact RC values:

```bash
python3 scripts/validate-stable-evidence.py \
  goreevault-stable-evidence.json \
  --expected-source-sha "<40-character RC source SHA>" \
  --expected-rc-tag "v0.3.0-rc.1" \
  --expected-manifest-digest "sha256:<64-hex manifest digest>"
```

The validator uses only the Python standard library and fails closed.

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
5. validates the evidence against the selected RC tag, source SHA, manifest, multi-user gate, product-wide Glaze UI gate, real-client matrix, WebAuthn, target environment, governance, and approvals;
6. only then promotes the exact RC manifest to the Stable version and `latest`.

A missing or invalid evidence asset blocks Stable publication.
