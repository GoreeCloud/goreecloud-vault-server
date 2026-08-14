# Contributing to GoreeVault

GoreeVault is a security-sensitive GoreeCloud project currently derived from Vaultwarden. Contributions are welcome, but compatibility and security take priority over aggressive renaming or refactoring.

## Development principles

1. Preserve Bitwarden-client compatibility unless a change explicitly introduces and documents a new compatibility boundary.
2. Keep authentication, cryptography, key handling, database migrations, and authorization changes small and reviewable.
3. Never use real GoreeCloud credentials, production vault exports, production databases, or private user data in tests.
4. Add or extend regression tests for behavior that changes.
5. Keep upstream provenance clear so Vaultwarden security and compatibility fixes remain practical to evaluate and merge.
6. Prefer GoreeVault-specific product identity at presentation and deployment boundaries before renaming internal compatibility identifiers.

## Pull requests

A pull request should explain:

- what behavior changes
- why the change is needed
- compatibility impact
- security impact
- migration or rollback implications
- tests performed

Changes affecting authentication, cryptography, key material, tokens, database migrations, attachments, organizations/collections, backup/restore, or client protocol behavior require dedicated test coverage before merge.

## Compatibility tests

Run the black-box compatibility harness before proposing server/API changes:

```bash
bash scripts/compat.sh
```

The harness uses only synthetic identities, opaque fake ciphertext, ephemeral PostgreSQL storage, and ephemeral server data.

## Upstream changes

Do not remove upstream attribution or license information. When importing an upstream Vaultwarden change, record the source commit or pull request when practical and resolve GoreeVault-specific conflicts explicitly rather than hiding them in broad refactors.

## Security reports

Do not file public exploit details. Follow `SECURITY.md` for vulnerability reporting.
