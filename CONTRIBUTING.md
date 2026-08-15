# Contributing to GoreeVault

GoreeVault is a security-sensitive GoreeCloud project currently derived from Vaultwarden. Compatibility, zero-knowledge security boundaries, GoreeCloud standards, multi-user isolation, Glaze UI, and evidence-backed readiness take priority over aggressive renaming or refactoring.

## Development principles

1. Preserve Bitwarden-client compatibility unless a change explicitly introduces, documents, and tests a new compatibility boundary.
2. Preserve individual-user identity, private-vault isolation, organization/collection authorization, and session/device lifecycle behavior. GoreeVault is not an administrator-only single-user application.
3. Keep authentication, cryptography, key handling, token behavior, authorization, database migrations, and storage changes small and reviewable.
4. Never use real GoreeCloud credentials, production vault exports, production databases, production backups, or private user data in tests.
5. Add or extend regression coverage for every behavior that changes.
6. Keep upstream provenance clear so Vaultwarden security and compatibility fixes remain practical to evaluate and merge.
7. Prefer GoreeVault product identity at presentation and deployment boundaries before renaming internal compatibility identifiers.
8. Every GoreeVault-controlled user interface must follow `docs/GLAZE-UI.md` and the shared GoreeCloud Glaze UI Design Language.
9. Production-readiness claims require exact-artifact evidence defined by `docs/PRODUCTION-READINESS.md`; a successful build alone is not production authorization.
10. Follow `docs/REPOSITORY-STRUCTURE.md` before adding top-level components or moving compatibility-sensitive source.

## Pull requests

A pull request should explain:

- what behavior changes;
- why the change is needed;
- compatibility impact;
- multi-user/authorization impact;
- security/privacy impact;
- migration and rollback implications;
- deployment/operational impact where applicable;
- Glaze UI/accessibility impact for user-facing changes;
- repository structure/ownership impact where applicable;
- exact tests and evidence performed.

Changes affecting authentication, cryptography, key material, tokens, user isolation, database migrations, attachments, organizations/collections, backup/restore, client protocol behavior, release workflows, production deployment, or security exceptions require dedicated regression coverage before merge.

## Required validation

Run the checks relevant to the change before proposing promotion.

For repository identity, structure, and readiness contracts:

```bash
python3 scripts/validate-repository-readiness.py
```

For server/API and multi-user compatibility changes:

```bash
bash scripts/compat.sh
```

For GoreeVault-owned browser presentation changes:

```bash
node --check src/static/scripts/admin.js
python3 scripts/validate-glaze-ui.py
```

For production deployment changes:

```bash
bash scripts/validate-production-deployment.sh
```

For Stable evidence changes:

```bash
python3 scripts/validate-stable-evidence.py docs/stable-evidence.example.json --allow-placeholders
```

The compatibility harness uses only synthetic identities, opaque fake ciphertext, ephemeral PostgreSQL storage, and ephemeral server data.

## Multi-user boundary

Multi-user readiness is a mandatory GoreeCloud production gate for GoreeVault.

Changes must not weaken:

- individual user accounts;
- unrelated-user private-data isolation;
- user-owned resource authorization;
- organization membership and role boundaries;
- collection permissions;
- permission-change and member-removal enforcement;
- device/session invalidation;
- the separation between private network access and application authorization.

A regression in an applicable multi-user boundary blocks release even if basic login or sync continues to work.

## Glaze UI and browser privacy

GoreeVault-owned browser surfaces must not add remote fonts, remote JavaScript, remote stylesheets, analytics, behavioral tracking, telemetry SDKs, advertising resources, or externally hosted branding assets.

Material UI changes must preserve keyboard access, visible focus, practical 44-pixel targets, System/Light/Dark behavior, reduced-motion support, increased-contrast/forced-colors fallbacks, responsive layouts, and textual state meaning. Source-level Glaze checks are required but do not replace representative browser/accessibility review before Stable.

The bundled Bitwarden-compatible web vault is a temporary compatibility dependency. It is not a permanent Glaze UI exception. Under the current GoreeCloud baseline, Stable product promotion remains blocked until GoreeVault owns the primary browser vault under Glaze UI or a separately approved material exception satisfies the full GoreeCloud exception standard.

## Production deployment

Production files are security policy, not convenience examples. Changes to `deploy/compose.production.yaml`, `deploy/.env.production.example`, or the production validator must preserve immutable image digests, the canonical `https://vault.goreecloud.com` origin, trusted reverse-proxy TLS termination, loopback-only backend publication, internal PostgreSQL networking, non-root/capability-free steady-state runtime, closed registration, and disabled-by-default `/admin`.

Do not deploy a branch or image merely because CI is green. Follow `docs/PRODUCTION-READINESS.md` and `docs/PRODUCTION-DEPLOYMENT.md`.

## Upstream changes

Do not remove upstream attribution or license information. When importing an upstream Vaultwarden change, record the source commit or pull request when practical and resolve GoreeVault-specific conflicts explicitly rather than hiding them in broad refactors.

Upstream merges must be revalidated against GoreeVault authentication, multi-user authorization, compatibility, security, production deployment, recovery, migration/rollback, and Glaze presentation boundaries as applicable.

## Security reports

Do not file public exploit details. Follow `SECURITY.md` for vulnerability reporting.
