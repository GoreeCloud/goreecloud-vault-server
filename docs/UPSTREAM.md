# GoreeVault Upstream Tracking

## Purpose

GoreeVault begins from Vaultwarden and must keep a deliberate, reviewable upstream relationship during the compatibility phase.

Upstream tracking is a security and compatibility control. A green GoreeVault branch is not sufficient release evidence if an applicable newer Vaultwarden security or client-compatibility fix has not been evaluated.

## Provenance baseline

- Upstream project: Vaultwarden
- Upstream repository: `dani-garcia/vaultwarden`
- Initial GoreeVault baseline: `0cefa4cca7c9f2a5579dd290f78193b543818c51`
- License: AGPL-3.0-only

Preserve upstream copyright, license, attribution, and source-availability obligations.

## Recommended local remotes

```bash
git remote -v
git remote add upstream https://github.com/dani-garcia/vaultwarden.git
```

If `upstream` already exists, verify its URL instead of adding a duplicate remote.

## Review workflow

```bash
git fetch --prune upstream

git log --oneline --decorate --graph \
  0cefa4cca7c9f2a5579dd290f78193b543818c51..upstream/main
```

Before importing an upstream change:

1. identify the upstream commit or pull request;
2. classify its security, compatibility, database, authentication, authorization, UI, dependency, deployment, and recovery impact;
3. determine whether GoreeVault already contains an equivalent fix;
4. import through a reviewed GoreeVault branch/PR rather than directly into a release branch;
5. resolve GoreeVault-specific conflicts deliberately;
6. rerun the exact-head GoreeVault gates that apply;
7. record the upstream source and validation evidence.

Do not automatically deploy an upstream merge to production.

## Security and compatibility priority

Applicable upstream changes receive elevated review priority when they affect:

- authentication or token handling;
- cryptography or key-management integration;
- WebAuthn/passkeys or TOTP;
- authorization or user/organization/collection isolation;
- attachments, Sends, imports, exports, or signed downloads;
- database migrations or persistence integrity;
- client API compatibility;
- rate limiting, proxy trust, or network-facing behavior;
- dependencies with security advisories;
- backup/recovery or migration behavior.

Branding-only differences do not justify delaying an applicable upstream security fix.

## Current upstream audit snapshot

**Audit date:** August 15, 2026

The GitHub comparison from the recorded GoreeVault baseline `0cefa4cca7c9f2a5579dd290f78193b543818c51` to `dani-garcia/vaultwarden:main` returned **identical**, with zero commits ahead of the baseline at the time of the audit.

Result for this snapshot:

- no newer upstream commit required import or disposition at that moment;
- no upstream delta was available to classify as an applicable security/compatibility fix;
- the audit does not eliminate the requirement to re-check upstream before an RC or Stable promotion.

This is a point-in-time record, not a permanent assertion that GoreeVault is current.

## Release gate

Before publishing a Release Candidate and again before Stable promotion:

1. fetch or query current upstream state;
2. compare the exact GoreeVault baseline/current upstream relationship;
3. identify any new upstream commits since the last recorded audit;
4. explicitly evaluate applicable security and compatibility changes;
5. import required fixes or document why a change is not applicable;
6. rerun exact-candidate validation after any import.

Stable promotion is denied when an applicable upstream Vaultwarden security fix has not been evaluated.
