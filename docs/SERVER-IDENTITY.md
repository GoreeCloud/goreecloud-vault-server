# GoreeCloud Vault Server Identity

## Status

Canonical and active.

## Canonical identity

- Official name: **GoreeCloud Vault Server**
- Short presentation: **Vault Server** when the GoreeCloud context is already explicit
- Repository: `GoreeCloud/goreecloud-vault-server`
- Canonical service address: `https://vault.goreecloud.com`
- Development model: GoreeCloud-maintained open-source fork with controlled fork-to-native transition
- Upstream foundation: Vaultwarden
- Upstream repository: `dani-garcia/vaultwarden`
- License: AGPL-3.0-only
- Design language: Glaze UI
- Security identity: Wardveil Security by GoreeCloud

## Naming decision

The former server name **GoreeVault Server** is retired for new server-facing use. Existing historical records may retain it when preserving chronology, but current server documentation and product surfaces must present **GoreeCloud Vault Server**.

`GoreeVault` is not automatically retired by this server rename. It remains the broader client-family and historical project identity for GoreeVault Web, Browser, Desktop, Mobile, and compatibility-era artifacts unless those products receive separate naming decisions.

## Required presentation boundary

Use **GoreeCloud Vault Server** in:

- repository landing documentation;
- server administration and error surfaces;
- server release notes and changelogs;
- deployment and recovery documentation;
- security and production-readiness records when referring specifically to the server;
- Google Drive project records and inventories when identifying this server component.

Do not rename compatibility-sensitive internal `vaultwarden` identifiers solely for branding. Internal identifiers, protocol semantics, migrations, and cryptographic behavior remain governed by compatibility and security review.

## Repository invariants

The repository-readiness validator must fail closed if the canonical README heading or the machine-readable server identity drifts from this document.

The machine-readable mirror is `docs/server-identity.json`.
