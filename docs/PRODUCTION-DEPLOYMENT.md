# GoreeVault Production Deployment Runbook

This runbook defines the minimum operator path for a GoreeVault production deployment. The development stack in `deploy/compose.yaml` is not a production release artifact and must not be used as Release Candidate or Stable evidence.

## Production invariants

1. Deploy GoreeVault by immutable OCI manifest digest, never by `:dev`, `:latest`, or a mutable semantic tag.
2. Deploy PostgreSQL by an explicitly recorded immutable image digest.
3. Terminate TLS at a trusted reverse proxy and set `GOREVAULT_DOMAIN` to the exact public HTTPS origin.
4. Keep PostgreSQL on the internal backend network with no host-published database port.
5. Bind GoreeVault HTTP to loopback only; the reverse proxy is the public entry point.
6. Run the steady-state GoreeVault server as an unprivileged numeric UID/GID, with all Linux capabilities dropped and a read-only root filesystem.
7. Keep public self-registration disabled unless an operator deliberately enables it.
8. Leave `ADMIN_TOKEN` blank unless the admin interface is intentionally enabled with an Argon2 PHC token and network-restricted access.
9. Create and verify a pre-upgrade backup before changing the GoreeVault or PostgreSQL image digest.
10. Rehearse migrations and rollback away from production data before promoting an RC.
11. Record the exact GoreeVault digest, PostgreSQL digest/version, source SHA, UID/GID, and deployment time for every production change.

## Files

- `deploy/compose.production.yaml` — published-image production topology
- `deploy/.env.production.example` — non-secret configuration template
- `docs/RC-EVIDENCE.md` — release-candidate evidence record
- `docs/CLIENT-COMPATIBILITY.md` — exact-client compatibility evidence

Store the real production environment file outside the repository with restrictive permissions. Never commit passwords, SMTP credentials, TOTP seeds, recovery codes, private keys, database dumps, or production `.env` files.

## Runtime privilege model

The upstream-compatible container image starts as root by default. The production Compose contract does not run the application that way.

A one-shot `data-init` service starts with only the privileges needed to establish `/data` ownership for `GOREVAULT_UID:GOREVAULT_GID`. It has no network, has a read-only root filesystem, and exits before the server starts. A marker tied to the configured UID/GID prevents recursive ownership repair on ordinary restarts; changing UID/GID intentionally triggers a new repair.

The `server` service then runs as the configured unprivileged numeric user, defaults to `10001:10001`, drops all Linux capabilities, sets `no-new-privileges`, uses a read-only root filesystem, and receives only `/data` plus a small hardened `/tmp` as writable filesystems. It listens on unprivileged container port 8080.

A first conversion from a root-run deployment can spend time recursively changing ownership of `/data`. Perform that conversion during a maintenance window and only after a verified backup.

## Prepare the deployment

Copy the production environment template to an operator-controlled location, for example `/etc/goreevault/production.env`, and set permissions to `0600`.

Set `GOREVAULT_IMAGE` to the exact approved RC/Stable manifest, for example:

```text
GOREVAULT_IMAGE=ghcr.io/goreecloud/goreevault-server@sha256:<64-hex-digest>
```

Set `POSTGRES_IMAGE` to the exact PostgreSQL manifest tested with the release. Record both digests in the release evidence.

Before starting, verify:

- both image references contain `@sha256:`
- `GOREVAULT_DOMAIN` begins with `https://`
- `GOREVAULT_UID` and `GOREVAULT_GID` are non-zero numeric IDs dedicated to GoreeVault
- the operator environment file is not tracked by Git

## Reverse proxy and network boundary

The Compose stack publishes GoreeVault only on `127.0.0.1:${GOREVAULT_HTTP_PORT}`. The trusted reverse proxy should be the only public path to the service and should provide TLS, preserve the original host/scheme, and support WebSocket upgrades.

PostgreSQL has no published host port and is attached only to the internal `goreevault-backend` network.

For GoreeCloud, keep administrative access separate from ordinary vault access. The safest default is to leave `/admin` disabled. If it is enabled later, restrict that route to the administrative network/NetBird policy rather than exposing it broadly at the public edge.

## First start

From the repository checkout that contains the approved deployment files:

```bash
docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  config

docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  pull
docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  up -d
```

Do not use the first production start as the first migration rehearsal. The candidate must already have passed disposable migration/rollback and recovery testing.

Verify:

- `data-init` exited successfully
- PostgreSQL and GoreeVault are healthy
- `docker inspect` reports the GoreeVault server running with the expected non-zero UID/GID
- the server has a read-only root filesystem and no effective application capabilities are required
- the public HTTPS origin returns the expected GoreeVault configuration
- registration policy is closed
- login/sync works with an approved client
- no PostgreSQL port is reachable from the public edge
- reverse-proxy and application logs contain no unexpected secrets or credentials

## Pre-upgrade backup

Take a backup before every GoreeVault or PostgreSQL image change. Stop the application first so attachment/file state cannot change while it is copied; PostgreSQL may remain running for the logical dump.

Example outline:

```bash
BACKUP_DIR="/srv/goreevault/backups/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  stop server

docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  exec -T postgres sh -c \
  'pg_dump --format=custom --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  > "${BACKUP_DIR}/postgres.dump"

docker cp goreevault-server:/data "${BACKUP_DIR}/data"
sha256sum "${BACKUP_DIR}/postgres.dump" > "${BACKUP_DIR}/SHA256SUMS"
tar -C "${BACKUP_DIR}" -cf - data | sha256sum >> "${BACKUP_DIR}/SHA256SUMS"

docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  start server
```

Encrypt and copy backups to the approved backup destination. A backup is not considered valid until restoration has been tested in an isolated environment.

## Upgrade by digest

1. Confirm the target digest is the exact artifact approved in the RC evidence.
2. Complete the pre-upgrade backup above.
3. Change only the intended immutable image reference(s) in the operator environment file.
4. If UID/GID changes, schedule time for the data initializer to re-own `/data`.
5. Run `docker compose pull` and inspect the resolved image digests.
6. Run `docker compose up -d`.
7. Wait for healthy state and execute the production smoke/client checks.
8. Record the deployment time, old digest, new digest, PostgreSQL digest/version, UID/GID, and outcome.

Do not promote a different image merely because it shares the same semantic version or source commit.

## Rollback

If an application-only regression occurs and the tested storage contract remains backward-compatible, restore the previously recorded GoreeVault image digest and restart the stack.

If migrations or storage state may have changed incompatibly, do not guess. Stop the application and restore the exact pre-upgrade PostgreSQL dump plus `/data` backup into an isolated or replacement stack according to the tested recovery procedure. Preserve the failed deployment state until incident evidence has been collected.

The ability to point at an older container is not, by itself, proof of rollback safety.

## Monitoring and operational checks

At minimum monitor:

- container health and restart loops
- GoreeVault `/alive` health
- reverse-proxy TLS/certificate expiry
- filesystem capacity for PostgreSQL, `/data`, and backups
- backup completion plus scheduled restore rehearsal
- authentication/2FA anomalies and security-event retention
- upstream Vaultwarden security releases and GoreeVault dependency/security alerts
- unexpected changes to the server UID/GID, writable filesystem set, or container capabilities

Never place vault contents, master passwords, tokens, TOTP seeds, recovery codes, session cookies, private keys, or unredacted database connection strings into monitoring labels or alerts.

## Repository controls required before Stable

Before the first Stable promotion, verify and record:

- protected GitHub Actions `release` environment exists
- at least one release reviewer is required and self-review is prevented
- `main` is protected against unreviewed/direct release-source changes
- GoreeCloud CODEOWNERS applies to runtime, workflow, security, deployment, migration, test, and scanner-exception surfaces
- GitHub Dependabot vulnerability alerts are enabled
- repository default Actions token permissions are read-only
- secret scanning is enabled/verified
- GoreeVault source and built-image Trivy gates are green on the exact candidate
- every Trivy exception is exact-ID, documented, time-bounded, and revalidated before expiry
- the published RC digest passed the real supported-client matrix and actual WebAuthn/passkey test

A missing repository control or unresolved fixed HIGH/CRITICAL vulnerability blocks Stable promotion.
