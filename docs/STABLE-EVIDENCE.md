# GoreeVault Stable Release Evidence

Stable promotion must be backed by one machine-readable evidence record named
`goreevault-stable-evidence.json` attached to the matching Release Candidate
GitHub release.

The evidence record is not a substitute for testing. It is the fail-closed handoff
between completed manual/operational validation and the Stable promotion workflow.

## Why the evidence lives on the RC release

GoreeVault Stable must promote the exact source commit and exact multi-architecture
OCI manifest that were tested as the Release Candidate. Committing evidence after
RC testing would change the source SHA and invalidate that guarantee.

For that reason:

1. publish an RC only after automated RC gates pass;
2. test the exact RC artifact;
3. create `goreevault-stable-evidence.json` from `docs/stable-evidence.example.json`;
4. validate it locally with `scripts/validate-stable-evidence.py`;
5. attach the validated file to the matching RC GitHub release;
6. create the Stable tag only after repository governance and release-environment
   approval are complete.

The Stable release workflow downloads that exact asset from the selected RC release
and rejects promotion when the file is missing, malformed, incomplete, references a
different source SHA, or references a different OCI manifest digest.

## Required evidence

The record must contain:

- exact RC tag;
- exact 40-character source commit SHA;
- exact GoreeVault multi-architecture OCI manifest digest;
- digest-pinned PostgreSQL image reference;
- bundled web-vault compatibility asset identification;
- Central Time-aware or otherwise offset-aware collection/test timestamps;
- real-client evidence for web, Chromium extension, Firefox extension, desktop,
  Android, and CLI clients;
- real WebAuthn/passkey registration and authentication evidence;
- target-environment production rehearsal evidence;
- repository and release-governance verification;
- at least one explicit reviewer approval record.

Every required client must pass:

- sign-in and unlock;
- full sync;
- create/update/delete;
- attachments;
- organization/collection behavior;
- TOTP;
- refresh-token rotation/replay behavior;
- logout and device/session invalidation.

## Target-environment evidence

The target rehearsal must verify the production contract at
`https://vault.goreecloud.com`, including:

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

Secret scanning, push protection, and private vulnerability reporting must be
recorded as `pass` or `not_supported`. `not_supported` is acceptable only when the
GitHub repository/account capability is genuinely unavailable, not as a waiver.

## Local validation

Use the exact RC values:

```bash
python3 scripts/validate-stable-evidence.py \
  goreevault-stable-evidence.json \
  --expected-source-sha "<40-character RC source SHA>" \
  --expected-rc-tag "v0.2.0-rc.1" \
  --expected-manifest-digest "sha256:<64-hex manifest digest>"
```

The validator uses only the Python standard library and fails closed.

## Upload to the matching RC release

After local validation, attach the file to the matching RC GitHub release using an
approved administrative workflow. One supported CLI form is:

```bash
gh release upload v0.2.0-rc.1 \
  goreevault-stable-evidence.json \
  --clobber
```

Do not upload evidence to a different RC release, rename the canonical asset, or
reuse evidence from another source SHA or manifest digest.

## Stable promotion behavior

On a Stable tag, `.github/workflows/goreevault-release.yml`:

1. locates the latest matching RC tag;
2. verifies the Stable tag points to the same source commit;
3. resolves the exact RC OCI manifest digest;
4. downloads `goreevault-stable-evidence.json` from that RC release;
5. validates the evidence against the selected RC tag, source SHA, and manifest;
6. only then promotes the exact RC manifest to the Stable version and `latest`.

A missing or invalid evidence asset blocks Stable publication.
