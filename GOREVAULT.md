# GoreeVault Server

GoreeVault is GoreeCloud's self-hosted, zero-knowledge credential platform.

## Product direction

This repository begins as a compatibility-focused derivative of Vaultwarden so GoreeCloud can establish a secure server, migration path, recovery model, deployment contract, and native product identity without inventing a new password-manager protocol or cryptographic system prematurely.

The long-term product is GoreeCloud-owned: GoreeVault Server plus GoreeVault Web, Browser, Desktop, and Mobile clients. Native clients will adopt the GoreeCloud Glaze UI Design Language and preserve client-side encryption/zero-knowledge behavior.

## Current compatibility boundary

The server keeps upstream-compatible cryptographic behavior, Bitwarden Client API behavior, database internals, migrations, and selected internal `vaultwarden` identifiers where those preserve compatibility and upstream maintainability.

GoreeVault-owned presentation surfaces use GoreeVault identity and Glaze UI. The bundled upstream-compatible web vault is a transitional compatibility asset until GoreeVault Web replaces or fully owns that presentation layer. Product-wide Glaze conformance is not claimed before that transition.

## Upstream provenance

- Upstream project: Vaultwarden
- Upstream repository: `dani-garcia/vaultwarden`
- Initial GoreeVault baseline: `0cefa4cca7c9f2a5579dd290f78193b543818c51`
- License: AGPL-3.0-only

The original `LICENSE.txt`, copyright notices, attribution, and source-availability obligations must remain intact.

## Compatibility policy

Until GoreeVault owns and supports native clients, server changes must preserve compatibility with the approved Bitwarden client matrix. Compatibility-breaking changes require explicit architectural approval, migration/rollback planning, and client regression evidence.

The compatibility harness treats encrypted vault contents as opaque data because decryption is a client responsibility.

## Security policy

Do not invent cryptographic primitives. Do not replace encryption, KDF, password hashing, WebAuthn/passkey, or token-signing behavior merely for branding or code ownership. Security-sensitive rewrites are separate reviewed projects with threat-model and regression updates.

Production clients use `https://vault.goreecloud.com`; TLS terminates at the trusted GoreeCloud reverse proxy and the HTTP backend must not be directly publicly exposed.

## GoreeCloud standards

GoreeVault development follows the repository contracts in:

- `docs/GLAZE-UI.md` — GoreeCloud Glaze UI presentation/accessibility/privacy contract;
- `docs/SECURITY-MODEL.md` and `SECURITY.md` — zero-knowledge and security boundaries;
- `docs/PRODUCTION-DEPLOYMENT.md` — hardened deployment contract;
- `docs/PRODUCTION-READINESS.md` — Release Candidate and Stable evidence/governance gates;
- `docs/UPSTREAM.md` — upstream tracking and review expectations.

A successful build or semantic version does not authorize production. Stable promotion requires the exact-artifact evidence and repository/target-environment gates defined by the readiness policy.
