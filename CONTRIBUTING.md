# Contributing to GoreeVault

GoreeVault is a security-sensitive GoreeCloud project currently derived from Vaultwarden. Compatibility, zero-knowledge security boundaries, GoreeCloud standards, and evidence-backed readiness take priority over aggressive renaming or refactoring.

## Development principles

1. Preserve Bitwarden-client compatibility unless a change explicitly introduces, documents, and tests a new compatibility boundary.
2. Keep authentication, cryptography, key handling, token behavior, authorization, database migrations, and storage changes small and reviewable.
3. Never use real GoreeCloud credentials, production vault exports, production databases, production backups, or private user data in tests.
4. Add or extend regression coverage for every behavior that changes.
5. Keep upstream provenance clear so Vaultwarden security and compatibility fixes remain practical to evaluate and merge.
6. Prefer GoreeVault product identity at presentation and deployment boundaries before renaming internal compatibility identifiers.
7. Every GoreeVault-owned user interface must follow `docs/GLAZE-UI.md` and the shared GoreeCloud Glaze UI Design Language.
8. Production-readiness claims require exact-artifact evidence defined by `docs/PRODUCTION-READINESS.md`; a successful build alone is not production authorization.

## Pull requests

A pull request should explain:

- what behavior changes;
- why the change is needed;
- compatibility impact;
- security/privacy impact;
- migration and rollback implications;
- deployment/operational impact where applicable;
- Glaze UI/accessibility impact for user-facing changes;
- exact tests and evidence performed.

Changes affecting authentication, cryptography, key material, tokens, database migrations, attachments, organizations/collections, backup/restore, client protocol behavior, release workflows, production deployment, or security exceptions require dedicated regression coverage before merge.

## Required validation

Run the checks relevant to the change before proposing promotion.

For server/API compatibility changes:

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

The compatibility harness uses only synthetic identities, opaque fake ciphertext, ephemeral PostgreSQL storage, and ephemeral server data.

## Glaze UI and browser privacy

GoreeVault-owned browser surfaces must not add remote fonts, remote JavaScript, remote stylesheets, analytics, behavioral tracking, telemetry SDKs, advertising resources, or externally hosted branding assets.

Material UI changes must preserve keyboard access, visible focus, practical 44-pixel targets, System/Light/Dark behavior, reduced-motion support, increased-contrast/forced-colors fallbacks, responsive layouts, and textual state meaning. Source-level Glaze checks are required but do not replace representative browser/accessibility review before Stable.

The bundled Bitwarden-compatible web vault is currently a transitional upstream compatibility asset. Do not claim product-wide Glaze conformance until GoreeVault Web replaces or fully owns that presentation layer under the approved compatibility contract.

## Production deployment

Production files are security policy, not convenience examples. Changes to `deploy/compose.production.yaml`, `deploy/.env.production.example`, or the production validator must preserve immutable image digests, the canonical `https://vault.goreecloud.com` origin, trusted reverse-proxy TLS termination, loopback-only backend publication, internal PostgreSQL networking, non-root/capability-free steady-state runtime, closed registration, and disabled-by-default `/admin`.

Do not deploy a branch or image merely because CI is green. Follow `docs/PRODUCTION-READINESS.md` and `docs/PRODUCTION-DEPLOYMENT.md`.

## Upstream changes

Do not remove upstream attribution or license information. When importing an upstream Vaultwarden change, record the source commit or pull request when practical and resolve GoreeVault-specific conflicts explicitly rather than hiding them in broad refactors.

Upstream merges must be revalidated against GoreeVault authentication, compatibility, security, production deployment, recovery, migration/rollback, and Glaze presentation boundaries as applicable.

## Security reports

Do not file public exploit details. Follow `SECURITY.md` for vulnerability reporting.
