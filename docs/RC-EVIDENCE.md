# GoreeVault Release Candidate Evidence

Use this file as a template for each release candidate. Copy it into a versioned/datestamped evidence record or complete it in the release PR before promotion. Do not replace evidence from one source commit or OCI digest with results from another.

## Candidate identity

- RC tag:
- Target Stable version:
- Source commit SHA:
- OCI image: `ghcr.io/goreecloud/goreevault-server@sha256:`
- RC semantic image tag:
- Source-SHA image tag:
- Test environment/domain:
- Evidence collection date/time and timezone:
- Reviewer:

The OCI digest above is the artifact identity for this evidence cycle. Client, recovery, migration, and security approval must refer to this exact published manifest.

## Repository release controls

- Protected `release` environment exists: NOT VERIFIED
- Required release approval/protection rules verified: NOT VERIFIED
- `main` protection/ruleset verified: NOT VERIFIED
- Release tag points to a commit contained in `main`: NOT VERIFIED

## Automated build and runtime evidence

Record the GitHub Actions run URL/ID and conclusion for the exact candidate source commit.

| Gate | Run/reference | Result |
|---|---|---|
| GoreeVault CI | | NOT VERIFIED |
| Build | | NOT VERIFIED |
| Compatibility | | NOT VERIFIED |
| Destructive recovery | | NOT VERIFIED |
| Vaultwarden → GoreeVault → Vaultwarden migration/rollback | | NOT VERIFIED |
| WebAuthn challenge/rejection regression | | NOT VERIFIED |
| Concurrent refresh-token one-winner regression | | NOT VERIFIED |
| Release multi-arch OCI preflight | | NOT VERIFIED |
| Trivy repository/source scan | | NOT VERIFIED |
| Trivy built production-image scan | | NOT VERIFIED |
| Hadolint/templates/spell/zizmor | | NOT VERIFIED |

A skipped inherited/upstream-only check does not satisfy a GoreeVault gate.

## Supply-chain evidence

- AMD64 + ARM64 manifest verified: NOT VERIFIED
- BuildKit SBOM generated: NOT VERIFIED
- BuildKit maximum provenance generated: NOT VERIFIED
- GitHub OIDC/Sigstore artifact attestation verified for the candidate digest: NOT VERIFIED
- Published RC digest matches the image used for client testing: NOT VERIFIED
- Source-SHA image tag resolves to the candidate digest: NOT VERIFIED
- Stable publisher is configured to promote the latest matching RC manifest without rebuilding: NOT VERIFIED

## Backup, restore, and migration evidence

- PostgreSQL + `/data` destructive restore passed for this source commit: NOT VERIFIED
- Cipher ciphertext identity verified after restore: NOT VERIFIED
- Attachment hash/exact bytes verified after restore: NOT VERIFIED
- Forward handoff from the required Vaultwarden baseline passed: NOT VERIFIED
- Rollback to the required Vaultwarden baseline passed: NOT VERIFIED
- Exact production/currently-deployed baseline compatibility separately rehearsed when different from the pinned fork baseline: NOT VERIFIED / N/A

## Security disposition

- Fixed HIGH findings in enforced source/dependency scan: NOT REVIEWED
- Fixed CRITICAL findings in enforced source/dependency scan: NOT REVIEWED
- Fixed HIGH findings in enforced built-image scan: NOT REVIEWED
- Fixed CRITICAL findings in enforced built-image scan: NOT REVIEWED
- GoreeVault-specific authentication/authorization review disposition:
- Known security limitations accepted for this RC:

Any unresolved release-blocking finding keeps the candidate below Stable.

## Real client evidence

Complete `docs/CLIENT-COMPATIBILITY.md` against the exact OCI digest above.

- Web vault required rows complete: NO
- Chromium extension required rows complete: NO
- Firefox extension required rows complete: NO
- Desktop client required rows complete: NO
- Android client required rows complete: NO
- CLI required rows complete: NO
- Real WebAuthn/passkey registration and authentication with an actual authenticator: NO

## Stable promotion verification

Complete these after the Stable tag workflow finishes and before treating the release as successfully promoted:

- Stable tag points to the same source commit as the approved latest matching RC: NOT VERIFIED
- Stable semantic image tag resolves to the candidate RC digest above: NOT VERIFIED
- `latest` resolves to the candidate RC digest above: NOT VERIFIED
- Stable workflow did not rebuild the production image: NOT VERIFIED
- Stable-run GitHub artifact attestation references the same candidate digest: NOT VERIFIED

Any digest mismatch is a failed Stable promotion even when source SHAs match.

## Final promotion decision

- All automated RC gates green on this source commit: NO
- Release repository protections verified: NO
- Candidate OCI digest is immutable and recorded: NO
- Supply-chain evidence verified: NO
- Client matrix complete: NO
- Real authenticator passkey evidence complete: NO
- No unresolved release blocker: NO
- Approved for Stable promotion: NO
- Final approver/date:

Stable must use the same tested source commit **and exact tested RC OCI manifest**. Any source or artifact change requires a new RC evidence cycle.
