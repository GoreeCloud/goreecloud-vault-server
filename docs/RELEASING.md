# GoreeCloud Vault Server Release Process

GoreeCloud Vault Server release artifacts are built from GitHub Actions identity and published to the GoreeCloud GitHub Container Registry.

`GoreeVault` remains the broader client-family and historical product identity. Existing workflow names and compatibility-era evidence filenames may retain GoreeVault where changing them is operationally unnecessary; release-facing server artifact identity uses GoreeCloud Vault Server.

## Release tags

Supported release tags are:

- `vMAJOR.MINOR.PATCH`, for example `v0.2.0`
- `vMAJOR.MINOR.PATCH-rc.N`, for example `v0.2.0-rc.1`

The release workflow rejects tags outside those formats and rejects tags whose commit is not contained in `main`.

A Stable tag is not allowed to introduce new source or a newly rebuilt container after RC testing. For a Stable tag such as `v0.2.0`, the workflow resolves the latest matching `v0.2.0-rc.N` tag, requires both tags to point to the same source commit, and promotes the exact tested RC OCI manifest digest to `0.2.0` and `latest`. If there is no prior matching RC, the source commit differs, the source-SHA image differs, or the promoted digest changes, Stable publishing fails.

## Pre-tag release validation

Pull requests run the same PostgreSQL Debian Dockerfile as a non-publishing Linux AMD64 + ARM64 OCI build. The preflight enables the same BuildKit SBOM and maximum-provenance settings used by the publisher and validates that a multi-architecture OCI manifest digest is produced.

The tag publisher depends on this preflight job. An RC tag is therefore not the first time GoreeCloud Vault Server exercises the multi-architecture release-image path.

## Registry

The canonical container is:

`ghcr.io/goreecloud/goreecloud-vault-server`

Release candidates publish:

- the RC semantic tag, such as `0.2.0-rc.1`
- a source tag in the form `sha-<12-character-commit>`

The RC container is built with the target Stable application version (`0.2.0` for the example above); RC status is represented by the registry/GitHub release tag. This allows a tested RC manifest to be promoted without changing the application bits.

Stable promotion does **not** rebuild the container. It copies the exact latest matching RC manifest to:

- the Stable semantic tag, such as `0.2.0`
- `latest`

The workflow verifies both promoted references resolve to the exact RC digest. Release candidates never move `latest`.

## RC deployment identity

Release-candidate testing must use the exact published OCI manifest digest, for example:

`ghcr.io/goreecloud/goreecloud-vault-server@sha256:<candidate-digest>`

Record that digest in the RC evidence before running the client matrix. Do not substitute a local source build, the development image, `latest`, or only a mutable semantic tag when collecting release evidence.

`deploy/compose.yaml` is the GoreeCloud Vault Server **development** deployment and builds the server locally. It is not the source of truth for RC/Stable artifact validation.

## Supply-chain evidence

The RC publisher builds Linux AMD64 and ARM64 images with BuildKit provenance and SBOM generation enabled. After the multi-architecture image is pushed, GitHub Actions creates an artifact attestation for the manifest digest using GitHub OIDC/Sigstore identity and pushes the attestation to the registry.

Stable promotion operates on that already-published manifest by digest rather than rebuilding it. The Stable workflow verifies the source-SHA reference, Stable semantic tag, and `latest` all resolve to the tested RC manifest and creates a Stable-run artifact attestation for the same digest.

Deployments should pin the manifest digest whenever practical rather than relying only on a mutable tag.

## Required repository setup

Before the first GoreeCloud Vault Server RC tag is created:

1. Create a GitHub Actions environment named `release`.
2. Configure at least one required reviewer for that environment.
3. Enable prevention of self-review so the person who triggers a release cannot approve their own deployment.
4. Verify the `main` branch protection/ruleset used by GoreeCloud prevents unreviewed source from becoming the release source of truth.
5. Verify the release workflow can write packages, attestations, releases, and OIDC identity only through its scoped `GITHUB_TOKEN` permissions.

The release workflow has a tag-only `release-controls` job that reads the `release` environment through GitHub's API before publishing. It fails closed if the environment does not exist, has no required reviewer, or allows self-review. The publishing job depends on both this controls check and the multi-architecture image preflight.

This explicit check is required because GitHub can create a referenced but nonexistent environment automatically without protection rules. The `environment: release` declaration by itself is therefore **not** accepted as evidence of release approval protection.

The workflow uses the repository-provided `GITHUB_TOKEN`; no long-lived GHCR password is required.

## Promotion sequence

Before creating a release tag:

1. Merge only a stabilization commit for which required CI, compatibility, recovery, migration/rollback, security, and release-image preflight gates are green.
2. Confirm the protected `release` environment and source-branch protections are active.
3. Create an RC tag first and deploy that exact digest to the GoreeCloud test environment.
4. Complete the real supported-client matrix and restore/rollback rehearsal against the RC digest.
5. Create the Stable tag on the **same source commit** only after all release gates are satisfied.
6. Verify the Stable workflow promotes the exact tested RC digest to the Stable semantic tag and `latest` without rebuilding the image.

Never rebuild a different artifact for Stable after the RC digest has earned release approval.
