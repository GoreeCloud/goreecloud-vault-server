# GoreeVault Release Process

GoreeVault release artifacts are built from GitHub Actions identity and published to the GoreeCloud GitHub Container Registry.

## Release tags

Supported release tags are:

- `vMAJOR.MINOR.PATCH`, for example `v0.2.0`
- `vMAJOR.MINOR.PATCH-rc.N`, for example `v0.2.0-rc.1`

The release workflow rejects tags outside those formats and rejects tags whose commit is not contained in `main`.

A Stable tag is not allowed to introduce new source after RC testing. For a Stable tag such as `v0.2.0`, the release workflow resolves the latest matching `v0.2.0-rc.N` tag and requires both tags to point to the same source commit. If there is no prior matching RC, or the latest RC points to different source, Stable publishing fails.

## Pre-tag release validation

Pull requests run the same PostgreSQL Debian Dockerfile as a non-publishing Linux AMD64 + ARM64 OCI build. The preflight enables the same BuildKit SBOM and maximum-provenance settings used by the publisher and validates that a multi-architecture OCI manifest digest is produced.

The tag publisher depends on this preflight job. An RC tag is therefore not the first time GoreeVault exercises the multi-architecture release-image path.

## Registry

The canonical container is:

`ghcr.io/goreecloud/goreevault-server`

Every release publishes two immutable references:

- the semantic version tag, such as `0.2.0` or `0.2.0-rc.1`
- a source tag in the form `sha-<12-character-commit>`

Stable releases also update `latest`. Release candidates never move `latest`.

## RC deployment identity

Release-candidate testing must use the exact published OCI manifest digest, for example:

`ghcr.io/goreecloud/goreevault-server@sha256:<candidate-digest>`

Record that digest in the RC evidence before running the client matrix. Do not substitute a local source build, the development image, `latest`, or only a mutable semantic tag when collecting release evidence.

`deploy/compose.yaml` is the GoreeVault **development** deployment and builds the server locally. It is not the source of truth for RC/Stable artifact validation.

## Supply-chain evidence

The release workflow builds Linux AMD64 and ARM64 images with BuildKit provenance and SBOM generation enabled. After the multi-architecture image is pushed, GitHub Actions creates an artifact attestation for the manifest digest using GitHub OIDC/Sigstore identity and pushes the attestation to the registry.

Deployments should pin the manifest digest whenever practical rather than relying only on a mutable tag.

## Required repository setup

Before the first GoreeVault RC tag is created:

1. Create a GitHub Actions environment named `release`.
2. Configure explicit environment protection appropriate for a security-sensitive vault release, including required reviewer approval where the repository plan supports it.
3. Verify the `main` branch protection/ruleset used by GoreeCloud prevents unreviewed source from becoming the release source of truth.
4. Verify the release workflow can write packages, attestations, releases, and OIDC identity only through its scoped `GITHUB_TOKEN` permissions.

The workflow references `environment: release`, but that reference by itself is **not** proof that approval rules are configured. Do not create an RC tag until the repository-side environment protection has been verified.

The workflow uses the repository-provided `GITHUB_TOKEN`; no long-lived GHCR password is required.

## Promotion sequence

Before creating a release tag:

1. Merge only a stabilization commit for which required CI, compatibility, recovery, migration/rollback, security, and release-image preflight gates are green.
2. Confirm the protected `release` environment and source-branch protections are active.
3. Create an RC tag first and deploy that exact digest to the GoreeCloud test environment.
4. Complete the real Bitwarden client matrix and restore/rollback rehearsal against the RC digest.
5. Promote the same tested source commit to the Stable version tag only after all release gates are satisfied. The workflow independently enforces that the Stable tag resolves to the same commit as the latest matching RC tag.

Never rebuild a different source commit under the same release version.
