# GoreeVault Release Candidate Evidence

Use this file as the human-readable evidence index for each GoreeVault Release Candidate. Copy it into a versioned/datestamped evidence record or complete an equivalent retained release record before promotion. Do not overwrite evidence from one source commit, browser-vault asset, or OCI digest with results from another.

This record complements, but does not replace, the machine-readable `goreevault-stable-evidence.json` required for Stable promotion.

## Evidence-state vocabulary

Use only:

- `PASS` — verified for this exact candidate with retained evidence;
- `FAIL` — verified and failed; include a non-secret reference;
- `NOT VERIFIED` — no qualifying evidence yet;
- `N/A` — genuinely inapplicable; explain why and confirm the governing release contract permits N/A.

Do not convert an unsupported or untested requirement to `PASS` merely to complete the record.

## Candidate identity

- RC tag:
- Target Stable version:
- Source commit SHA:
- GoreeVault OCI image: `ghcr.io/goreecloud/goreevault-server@sha256:`
- Exact OCI manifest digest:
- RC semantic image tag:
- Source-SHA image tag:
- PostgreSQL image and immutable digest:
- Browser-vault asset/client name, version, and immutable identity:
- Test environment/domain:
- Evidence collection start date/time and timezone:
- Evidence collection completion date/time and timezone:
- Primary tester/operator:
- Reviewer:

The source SHA, GoreeVault manifest digest, PostgreSQL image, and browser-vault identity above define this evidence cycle. Client, recovery, migration, security, multi-user, target-environment, and release approval must refer to the same applicable artifacts.

## Parent/source qualification

- Candidate source is based on the approved GoreeVault maintained-fork baseline: NOT VERIFIED
- Upstream review completed according to `docs/UPSTREAM.md`: NOT VERIFIED
- Required upstream security/compatibility changes are dispositioned: NOT VERIFIED
- No unreviewed source or generated-file drift remains: NOT VERIFIED

## Repository release controls

Record the current GitHub repository state rather than assuming settings from a previous RC.

- `main` protected against direct/unreviewed release-source changes: NOT VERIFIED
- Required GoreeVault checks enforced: NOT VERIFIED
- CODEOWNERS review enforcement verified for protected surfaces: NOT VERIFIED
- Protected `release` environment exists: NOT VERIFIED
- Required release reviewer configured: NOT VERIFIED
- Release self-review prevention verified where supported: NOT VERIFIED
- Default GitHub Actions token permission is read-only: NOT VERIFIED
- Dependabot vulnerability alerts enabled: NOT VERIFIED
- Secret scanning state (`PASS` or contract-permitted `not_supported`): NOT VERIFIED
- Push protection state (`PASS` or contract-permitted `not_supported`): NOT VERIFIED
- Private vulnerability reporting state (`PASS` or contract-permitted `not_supported`): NOT VERIFIED
- Release tag points to a commit permitted by repository governance: NOT VERIFIED

A repository setting that cannot be read through an integration remains `NOT VERIFIED`; absence of visibility is not evidence of success or failure.

## Automated exact-head source gates

Record the GitHub Actions run URL/ID and conclusion for the exact candidate source commit.

| Gate | Run/reference | Result |
|---|---|---|
| Build | | NOT VERIFIED |
| GoreeVault CI | | NOT VERIFIED |
| GoreeVault Compatibility | | NOT VERIFIED |
| GoreeVault Recovery | | NOT VERIFIED |
| GoreeVault Migration Handoff | | NOT VERIFIED |
| GoreeVault Security Scan | | NOT VERIFIED |
| GoreeVault Release multi-architecture preflight | | NOT VERIFIED |
| GoreeVault Production Deployment Validation | | NOT VERIFIED |
| GoreeVault Repository Readiness | | NOT VERIFIED |
| GoreeVault Stable Evidence self-tests | | NOT VERIFIED |
| GoreeVault Evidence Tooling | | NOT VERIFIED |
| GoreeVault Glaze UI server-owned surfaces | | NOT VERIFIED |
| Check templates | | NOT VERIFIED |
| Hadolint | | NOT VERIFIED |
| Code Spell Checking | | NOT VERIFIED |
| Security Analysis with zizmor | | NOT VERIFIED |

Where a broader workflow contains multiple release-critical jobs, retain enough detail to prove the required jobs passed rather than recording only an ambiguous workflow name.

A skipped inherited/upstream-only check does not satisfy a GoreeVault gate unless the GoreeVault release contract explicitly classifies that skip as acceptable.

## Automated authentication and multi-user regression evidence

Record the exact workflow/test reference for each required server-side behavior:

- fresh PostgreSQL startup and migrations: NOT VERIFIED
- database-backed health/readiness behavior: NOT VERIFIED
- closed registration policy: NOT VERIFIED
- isolated account creation/login: NOT VERIFIED
- unrelated-user private-vault isolation: NOT VERIFIED
- unauthorized cross-user access denial: NOT VERIFIED
- organization membership authorization: NOT VERIFIED
- collection authorization: NOT VERIFIED
- permission-change enforcement: NOT VERIFIED
- member-removal enforcement: NOT VERIFIED
- session/device invalidation: NOT VERIFIED
- personal cipher create/read/update/delete: NOT VERIFIED
- attachment lifecycle: NOT VERIFIED
- TOTP regression coverage: NOT VERIFIED
- WebAuthn challenge/rejection regression coverage: NOT VERIFIED
- single-use refresh-token rotation/replay rejection: NOT VERIFIED
- concurrent refresh-token consumption has exactly one winner: NOT VERIFIED

Automated synthetic coverage supports release qualification but does not replace the exact-candidate real-client, real-WebAuthn, or target-environment sections below.

## Supply-chain evidence

- AMD64 + ARM64 manifest verified: NOT VERIFIED
- Published RC manifest digest recorded: NOT VERIFIED
- BuildKit SBOM generated where required by the release workflow: NOT VERIFIED
- BuildKit provenance generated at the required level: NOT VERIFIED
- GitHub OIDC/Sigstore artifact attestation verified for the candidate digest: NOT VERIFIED
- Published RC digest matches the image used for real-client testing: NOT VERIFIED
- Source-SHA image tag resolves to the candidate digest: NOT VERIFIED
- PostgreSQL production image is digest-pinned: NOT VERIFIED
- Browser-vault production asset has immutable/traceable identity: NOT VERIFIED
- Stable publisher is configured to promote the approved matching RC manifest without rebuilding: NOT VERIFIED

## Backup, restore, and migration evidence

- PostgreSQL + `/data` destructive restore passed for this source commit: NOT VERIFIED
- Cipher ciphertext identity verified after restore: NOT VERIFIED
- Attachment hash/exact bytes verified after restore: NOT VERIFIED
- Forward handoff from the required Vaultwarden baseline passed: NOT VERIFIED
- Rollback to the required Vaultwarden baseline passed: NOT VERIFIED
- Exact currently deployed production baseline compatibility separately rehearsed when different from the pinned fork baseline: NOT VERIFIED / N/A
- Backup/restore evidence contains no reusable credentials or private production vault data: NOT VERIFIED

## Security disposition

- Enforced source/dependency scan has no unresolved release-blocking HIGH finding: NOT VERIFIED
- Enforced source/dependency scan has no unresolved release-blocking CRITICAL finding: NOT VERIFIED
- Enforced built-image scan has no unresolved release-blocking HIGH finding: NOT VERIFIED
- Enforced built-image scan has no unresolved release-blocking CRITICAL finding: NOT VERIFIED
- GoreeVault-specific authentication/authorization review disposition:
- Dependency/license review disposition:
- Known security limitations accepted for this RC:
- Security exceptions, owners, expiry/removal conditions:

Any unresolved release-blocking finding keeps the candidate below the maturity level that requires it.

## Real multi-user evidence

The final Stable evidence schema requires a `multi_user` section tied to real retained evidence. Record a non-secret reference proving:

- individual accounts/identities are used: NOT VERIFIED
- private vault isolation between unrelated users: NOT VERIFIED
- unauthorized cross-user access is denied: NOT VERIFIED
- organization membership boundaries are enforced: NOT VERIFIED
- collection authorization is enforced: NOT VERIFIED
- permission changes take effect: NOT VERIFIED
- member removal takes effect: NOT VERIFIED
- session/device invalidation works: NOT VERIFIED
- ordinary users do not depend on a shared administrator account: NOT VERIFIED
- evidence reference:
- tested at and timezone:

Do not record actual passwords, decrypted private vault values, TOTP seeds, recovery codes, or session tokens.

## Real client and WebAuthn evidence

Complete `docs/CLIENT-COMPATIBILITY.md` against the exact source SHA, OCI manifest digest, and browser-vault identity above.

The human matrix is mechanically aligned to the eight client checks required by Stable-evidence schema version 2.

- Web `kind: web` all eight required checks PASS: NO
- Chromium extension `kind: chromium_extension` all eight required checks PASS: NO
- Firefox extension `kind: firefox_extension` all eight required checks PASS: NO
- Desktop `kind: desktop` all eight required checks PASS: NO
- Android `kind: android` all eight required checks PASS: NO
- CLI `kind: cli` all eight required checks PASS: NO
- Real WebAuthn/passkey registration with actual supported authenticator PASS: NO
- Real WebAuthn/passkey authentication with that credential/path PASS: NO
- Client matrix evidence references reviewed for secrets/private data: NO

Under Stable-evidence schema version 2, a required `N/A`, `FAIL`, or `NOT TESTED` client check does not satisfy the final Stable gate.

## Target-environment rehearsal evidence

Exercise `docs/PRODUCTION-DEPLOYMENT.md` in the intended GoreeCloud target environment with the exact candidate artifacts.

Machine-observed or directly verified controls:

- canonical origin is `https://vault.goreecloud.com`: NOT VERIFIED
- GoreeVault backend bind is loopback-only: NOT VERIFIED
- trusted reverse proxy provides HTTPS/WSS: NOT VERIFIED
- PostgreSQL has no host-published port: NOT VERIFIED
- server runs as approved non-zero numeric UID/GID: NOT VERIFIED
- root filesystem is read-only: NOT VERIFIED
- all Linux capabilities are dropped: NOT VERIFIED
- `no-new-privileges` is active: NOT VERIFIED
- public registration is closed: NOT VERIFIED
- `/admin` remains disabled under current production policy: NOT VERIFIED
- GoreeVault and PostgreSQL images are immutable digests: NOT VERIFIED
- live GoreeVault image matches exact RC manifest digest: NOT VERIFIED
- pre-deployment backup created: NOT VERIFIED
- isolated restore rehearsed: NOT VERIFIED
- rollback recorded/rehearsed as applicable: NOT VERIFIED
- monitoring verified: NOT VERIFIED
- logs reviewed for sensitive-data minimization: NOT VERIFIED
- approved NetBird/private administrative path verified: NOT VERIFIED
- evidence timestamp and timezone:
- backup reference:
- rollback reference:

After the work actually occurs, `scripts/collect-target-evidence.py` may be used to produce the non-secret `target_environment` JSON object. The collector is read-only and does not create the backup, restore data, validate clients, configure networking, or authorize production.

- Collector output reviewed: NO
- Collector output contains no reusable secrets/private vault data: NO
- Collector output matches this exact candidate digest: NO

## Glaze UI evidence

### Server-owned surfaces

- GoreeVault Admin/error surfaces pass repository Glaze UI gate: NOT VERIFIED
- Transactional email presentation uses GoreeVault identity and approved email-safe Glaze treatment: NOT VERIFIED
- Server-owned presentation has no unapproved remote analytics/tracking dependency: NOT VERIFIED

### Product-wide browser ownership

The current bundled upstream-compatible browser vault is a temporary compatibility dependency. Under the current approved GoreeCloud path, it does **not** satisfy product-wide Stable Glaze UI ownership.

`docs/WEB-CLIENT-CONTRACT.md` defines the future GoreeVault Web boundary. Until that separate client is implemented and accepted, record:

- Primary production browser vault is GoreeCloud-owned: NO
- Product-wide Glaze UI conformance proven: NO
- System/Light/Dark acceptance proven: NO
- Keyboard/focus accessibility proven: NO
- Reduced-motion support proven: NO
- Increased-contrast support proven: NO
- Forced-colors/High Contrast support proven: NO
- Local-only presentation dependencies proven: NO
- No analytics/behavioral tracking proven: NO
- Browser/accessibility evidence reference:

These `NO` values do not prevent documenting a server RC when the governing roadmap permits that milestone, but they **do block product-wide Stable promotion** under the current approved path.

## Open readiness blockers reconciliation

Review `docs/OPEN-READINESS-BLOCKERS.md` immediately before RC sign-off.

- GitHub governance blocker closed or explicitly remains open below Stable: NO
- real client matrix blocker closed: NO
- real WebAuthn/passkey blocker closed: NO
- target-environment rehearsal blocker closed: NO
- product-wide Glaze UI ownership blocker closed: NO
- exact-RC Stable evidence/approval blocker closed: NO

Do not remove a blocker because work started; close it only when objective retained evidence satisfies the governing contract.

## RC decision

Use this section to decide whether the candidate qualifies for the specific RC milestone defined by `docs/ROADMAP.md` and `docs/PRODUCTION-READINESS.md`.

- All automated gates required for this RC milestone green on exact source commit: NO
- Candidate source SHA and OCI manifest are immutable and recorded: NO
- Required server-side multi-user/security/recovery/migration evidence complete: NO
- Required real-client matrix for this RC milestone complete: NO
- Required real WebAuthn evidence for this RC milestone complete: NO
- Required target-environment rehearsal for this RC milestone complete: NO
- Required repository governance for this RC milestone verified: NO
- No unresolved blocker that prevents this RC milestone: NO
- Approved as the stated GoreeVault Server RC milestone: NO
- RC approver/date/timezone:

Approval of a server RC does not imply product-wide Stable approval.

## Stable evidence assembly

Only after every Stable blocker is closed:

- prepare reviewed section files for `rc`, `multi_user`, `clients`, `webauthn`, `glaze_ui`, `target_environment`, `governance`, and `approvals`: NO
- verify every section contains only the exact schema value and no reusable secrets/private vault data: NO
- bind exact RC tag, source SHA, GoreeVault manifest digest, PostgreSQL image, and immutable browser-vault asset identity: NO
- verify all six real-client records have every schema-required check true: NO
- verify real WebAuthn registration/authentication evidence: NO
- verify product-wide Glaze UI evidence: NO
- verify target-environment collector/reviewed evidence: NO
- verify repository governance evidence: NO
- verify required reviewer approval: NO
- run `scripts/assemble-stable-evidence.py` successfully against the exact source SHA, RC tag, and manifest digest: NO
- independently run `scripts/validate-stable-evidence.py` successfully against the assembled canonical file: NO
- verify `goreevault-stable-evidence.json` is mode `0600` before upload: NO
- attach canonical `goreevault-stable-evidence.json` to the matching RC GitHub release: NO

The assembler does not create evidence or complete missing tests. It rejects placeholders, unknown/duplicate fields through the Stable validator, mismatched exact-RC identifiers, implicit overwrite, and symbolic-link output paths.

## Stable promotion verification

Complete these after the Stable tag workflow finishes and before treating the release as successfully promoted:

- Stable tag points to the same source commit as the approved matching RC: NOT VERIFIED
- Stable semantic image tag resolves to the candidate RC digest above: NOT VERIFIED
- `latest` resolves to the candidate RC digest above: NOT VERIFIED
- Stable workflow did not rebuild the production image: NOT VERIFIED
- Stable-run GitHub artifact attestation references the same candidate digest: NOT VERIFIED
- Stable workflow downloaded and validated the canonical evidence asset from the matching RC release: NOT VERIFIED

Any source, browser asset, or digest mismatch is a failed Stable promotion even when semantic versions look correct.

## Final Stable decision

- All Stable evidence sections validate against the exact RC: NO
- Repository/release protections verified: NO
- Candidate artifacts immutable and traceable: NO
- Supply-chain evidence verified: NO
- Multi-user evidence complete: NO
- Client matrix complete: NO
- Real authenticator passkey evidence complete: NO
- Target-environment evidence complete: NO
- Product-wide GoreeVault-owned Glaze UI evidence complete: NO
- Backup/restore/migration/rollback evidence complete: NO
- No unresolved Stable blocker: NO
- Approved for Stable promotion: NO
- Final approver/date/timezone:

Stable must use the same tested source commit **and exact tested RC OCI manifest**. Any source or artifact change requires a new evidence cycle unless the release contract explicitly proves artifact equivalence without rebuilding or changing behavior.
