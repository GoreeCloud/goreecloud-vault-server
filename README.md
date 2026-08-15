# GoreeVault Server

GoreeVault Server is GoreeCloud's self-hosted, zero-knowledge credential server. It is a GoreeCloud-maintained derivative of Vaultwarden that preserves Bitwarden-client compatibility while GoreeCloud builds an independently governed, recoverable, security-reviewed credential platform.

> [!IMPORTANT]
> GoreeVault is under active stabilization. The current source line is **not approved for GoreeCloud Stable production use**. Release Candidate and Stable promotion are controlled by the evidence gates in `docs/PRODUCTION-READINESS.md`.

## Product role

GoreeVault is designed to provide secure multi-user credential storage for individual GoreeCloud users while preserving private-data boundaries between accounts and the client-side encryption model inherited from the compatible Bitwarden/Vaultwarden ecosystem.

The long-term GoreeVault product family is:

- **GoreeVault Server** — this repository; API, persistence, authentication, authorization, recovery, and server-side operations;
- **GoreeVault Web** — planned GoreeCloud-owned browser vault using Glaze UI;
- **GoreeVault Browser** — planned Firefox and Chromium extensions;
- **GoreeVault Desktop** — planned desktop client;
- **GoreeVault Mobile** — planned Android-first mobile client with additional platform planning as appropriate.

GoreeVault does not invent new cryptographic primitives merely to create product differentiation. Compatibility-sensitive cryptography, KDF behavior, token behavior, WebAuthn/passkey handling, database migrations, and protocol semantics remain security-reviewed boundaries.

## Current status

The current stabilization chain has established automated evidence for:

- PostgreSQL startup and migrations;
- closed-registration behavior;
- isolated multi-user account behavior and organization/collection authorization boundaries;
- login, sync, personal cipher CRUD, attachments, TOTP, and WebAuthn compatibility behavior;
- single-use and concurrent refresh-token replay protection;
- destructive PostgreSQL plus `/data` recovery rehearsal;
- Vaultwarden-to-GoreeVault migration and rollback rehearsal;
- source and production-image HIGH/CRITICAL vulnerability gates;
- AMD64/ARM64 OCI release-image preflight;
- digest-pinned hardened production Compose validation;
- GoreeVault-owned Glaze UI source conformance;
- fail-closed Stable-release evidence validation.

Stable remains blocked until every requirement in `docs/PRODUCTION-READINESS.md` is satisfied, including real supported-client testing, a real WebAuthn/passkey path, target-environment evidence, repository governance, multi-user readiness evidence, and product-wide Glaze UI compliance.

## Glaze UI

**Glaze UI is mandatory for every GoreeVault-controlled user-facing interface.**

The server-owned Admin and error surfaces use the repository-local Glaze UI contract in `docs/GLAZE-UI.md`. The bundled upstream-compatible web vault is currently a transitional compatibility dependency and is not treated as a permanent production exception. GoreeVault will not claim product-wide Glaze UI compliance or Stable readiness while that upstream presentation remains the primary browser vault unless a separately approved GoreeCloud exception satisfies the full exception standard.

The planned GoreeVault Web client is the intended product-wide Glaze UI browser surface.

## Multi-user and privacy model

GoreeVault is not a single-user application. Production readiness requires:

- an individual account or identity for each user;
- authorization boundaries between users;
- isolation of private vault data;
- controlled organization and collection sharing;
- no shared administrator account as a substitute for user identity;
- security controls that remain effective even when private networking is present.

The server treats encrypted vault content as opaque client-controlled ciphertext where required by the compatible zero-knowledge model.

## Security posture

Security-sensitive work is intentionally conservative.

- Do not invent or casually replace cryptographic primitives.
- Do not use production vault exports, production databases, real credentials, or private user data in tests.
- Do not directly expose the GoreeVault backend listener to the public internet.
- Production HTTPS/WSS terminates at the trusted GoreeCloud reverse proxy.
- Production image references must be immutable digests.
- Public registration is closed by default.
- `/admin` is disabled by default in the production deployment contract.
- Secrets and reusable credentials must remain outside source control and ordinary documentation.

See `SECURITY.md`, `docs/SECURITY-MODEL.md`, and `docs/PRODUCTION-DEPLOYMENT.md`.

## Repository structure

The repository is intentionally split by responsibility:

```text
.github/       GitHub Actions, CODEOWNERS, release and security automation
deploy/        GoreeCloud production deployment contract and environment template
docker/        upstream-compatible image build inputs and generated Dockerfiles
docs/          GoreeVault architecture, readiness, Glaze UI, recovery and governance records
migrations/    database migrations
scripts/       validation, compatibility, release-readiness and operational checks
src/           Rust server runtime plus GoreeVault-owned server presentation
tests/         compatibility and release-blocking regression coverage
```

See `docs/REPOSITORY-STRUCTURE.md` before adding a new top-level component or moving a compatibility-sensitive file.

## Development validation

Run the checks relevant to the change. Important GoreeVault-owned validators include:

```bash
python3 scripts/validate-repository-readiness.py
python3 scripts/validate-glaze-ui.py
bash scripts/validate-production-deployment.sh
bash scripts/compat.sh
```

Stable evidence is validated with:

```bash
python3 scripts/validate-stable-evidence.py goreevault-stable-evidence.json \
  --expected-source-sha '<40-character RC source SHA>' \
  --expected-rc-tag 'vX.Y.Z-rc.N' \
  --expected-manifest-digest 'sha256:<64-hex manifest digest>'
```

GitHub Actions runs the repository's release-blocking checks against exact pull-request revisions.

## Deployment boundary

Do not deploy from a floating image tag or copy an upstream `latest` example into GoreeCloud production.

The reviewed GoreeVault production model is defined by:

- `deploy/compose.production.yaml`;
- `deploy/.env.production.example`;
- `docs/PRODUCTION-DEPLOYMENT.md`;
- `scripts/validate-production-deployment.sh`.

The production contract requires immutable GoreeVault and PostgreSQL image digests, loopback-only backend publication, an internal database network, a non-root and capability-free steady-state server, a read-only root filesystem, and trusted reverse-proxy HTTPS/WSS.

## Upstream provenance

GoreeVault begins from Vaultwarden and deliberately keeps portions of the upstream architecture and internal identity where changing them would increase security risk, compatibility risk, or upstream-maintenance cost.

- Upstream project: **Vaultwarden**
- Upstream repository: `dani-garcia/vaultwarden`
- Initial GoreeVault baseline: `0cefa4cca7c9f2a5579dd290f78193b543818c51`
- License: **AGPL-3.0-only**

The original `LICENSE.txt`, copyright notices, attribution, and source-availability obligations remain part of this repository. See `GOREVAULT.md` and `docs/UPSTREAM.md` for the maintained-fork boundary.

GoreeVault is not affiliated with or endorsed by Bitwarden, Inc. Bitwarden is a trademark of its respective owner.

## Contributing and security reports

Read `CONTRIBUTING.md` before proposing changes. Compatibility, authorization, cryptography, persistence, release, deployment, and UI changes require evidence appropriate to their risk.

Do not publish exploit details in a public issue. Follow `SECURITY.md` for vulnerability reporting.
