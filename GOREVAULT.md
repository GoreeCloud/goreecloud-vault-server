# GoreeVault Server

GoreeVault is GoreeCloud's self-hosted zero-knowledge credential platform.

## v0.1.0 status

This repository begins as a compatibility-focused derivative of Vaultwarden. The first release keeps the upstream cryptographic behavior, Bitwarden Client API compatibility, database internals and `vaultwarden` binary/package identity intact while GoreeCloud establishes its own product surface, deployment model, CI and security governance.

## Upstream provenance

- Upstream project: Vaultwarden
- Upstream repository: `dani-garcia/vaultwarden`
- Initial GoreeVault baseline: `0cefa4cca7c9f2a5579dd290f78193b543818c51`
- License: AGPL-3.0-only

The original `LICENSE.txt`, copyright notices and source availability obligations must remain intact.

## Compatibility policy

Until GoreeVault owns native clients, server changes must preserve compatibility with supported Bitwarden clients. Compatibility-breaking changes require an architecture decision record, explicit migration path and client test coverage.

## Security policy

Do not invent cryptographic primitives. Do not replace encryption, KDF, password hashing, WebAuthn or token-signing behavior merely for branding or code ownership. Security-sensitive rewrites happen only as separately reviewed projects with tests and threat-model updates.
