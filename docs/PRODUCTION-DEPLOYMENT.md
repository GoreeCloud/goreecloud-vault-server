# GoreeVault Production Deployment

## Purpose

This runbook defines the minimum GoreeCloud production deployment contract for GoreeVault. It does not authorize production by itself. The development stack in `deploy/compose.yaml` remains development-only; production uses `deploy/compose.production.yaml` with immutable release artifacts.

## Production invariants

1. Deploy GoreeVault and PostgreSQL by immutable OCI manifest digest, never by `:latest`, `:dev`, or another mutable tag.
2. The canonical public origin is `https://vault.goreecloud.com`.
3. TLS terminates at the trusted GoreeCloud reverse proxy. The GoreeVault backend remains HTTP-only behind that trust boundary and must never be directly exposed to the public network.
4. The host-published GoreeVault backend port binds only to `127.0.0.1`.
5. PostgreSQL has no host-published port and uses only the internal `goreevault-backend` network.
6. The steady-state server runs as a dedicated non-root numeric UID/GID, drops all Linux capabilities, uses `no-new-privileges`, has a read-only root filesystem, and receives only explicitly declared writable storage.
7. The one-shot data initializer has no network and only the minimum ownership-related capabilities. Its success marker is created only after recursive ownership repair succeeds.
8. Public registration defaults closed.
9. `/admin` defaults disabled. If deliberately enabled later, use an Argon2 PHC token and restrict the route to the GoreeCloud administrative network/NetBird policy.
10. A verified backup and tested restore path are required before any production image change.
11. Migration and rollback must be rehearsed away from production data before a release candidate is promoted.
12. Every production change records the source SHA, GoreeVault image digest, PostgreSQL image digest/version, runtime UID/GID, deployment time, operator, and outcome.

## Files

- `deploy/compose.production.yaml` — production topology and runtime-hardening contract.
- `deploy/.env.production.example` — non-secret production configuration template.
- `scripts/validate-production-deployment.sh` — fail-closed structural validator.
- `scripts/collect-target-evidence.py` — read-only target-environment Stable evidence collector used only after real rehearsal work is complete.
- `docs/PRODUCTION-READINESS.md` — release and governance gates.
- `docs/RC-EVIDENCE.md` — release-candidate evidence record.
- `docs/CLIENT-COMPATIBILITY.md` — client compatibility evidence.
- `docs/STABLE-EVIDENCE.md` — complete exact-RC Stable evidence contract and collector usage.

The real production environment file belongs outside the repository and must be restricted to the operator account/root. Never commit passwords, SMTP credentials, TOTP seeds, recovery codes, private keys, database dumps, session material, or production `.env` files.

## Prepare

Copy the production environment template to an operator-controlled location such as `/etc/goreevault/production.env`, set permissions to `0600`, and replace every `CHANGEME` value.

Set the approved immutable artifacts, for example:

```text
GOREVAULT_IMAGE=ghcr.io/goreecloud/goreevault-server@sha256:<64-hex-digest>
POSTGRES_IMAGE=docker.io/library/postgres@sha256:<64-hex-digest>
```

Keep:

```text
GOREVAULT_DOMAIN=https://vault.goreecloud.com
SIGNUPS_ALLOWED=false
ADMIN_TOKEN=
```

Before first start, run:

```bash
bash scripts/validate-production-deployment.sh

docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  config
```

Do not proceed if the validator fails or if the rendered configuration differs from the reviewed production contract.

## Reverse proxy and network boundary

The reverse proxy is the only public entry point. It must provide HTTPS/WSS, preserve the original host and scheme, support WebSocket upgrades, and forward only to the loopback-published GoreeVault backend.

The backend listener must not be published on `0.0.0.0`, `::`, a public interface, host networking, or a directly routed public container address. PostgreSQL remains isolated on the internal backend network.

For GoreeCloud, ordinary vault access and infrastructure administration are separate concerns. If `/admin` is enabled later, restrict it to the administrative NetBird/network policy instead of exposing it at the ordinary public edge.

## First start

```bash
docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  pull

docker compose \
  --env-file /etc/goreevault/production.env \
  -f deploy/compose.production.yaml \
  up -d
```

Verify all of the following before accepting the deployment:

- `data-init` exited successfully;
- PostgreSQL and GoreeVault are healthy;
- the server is running as the approved non-zero UID/GID;
- the server root filesystem is read-only and no application capabilities are added;
- the backend host bind is loopback-only;
- `https://vault.goreecloud.com` returns the expected GoreeVault configuration through the reverse proxy;
- registration remains closed;
- `/admin` remains disabled unless a separately reviewed administrative-access change authorized it;
- approved client login, sync, create/update/delete, attachment, TOTP, and WebAuthn/passkey paths pass;
- PostgreSQL is not reachable from the public edge;
- logs do not contain secrets, vault contents, session cookies, recovery codes, TOTP seeds, private keys, or unredacted database credentials.

## Backup before changes

Before every GoreeVault or PostgreSQL image change, stop the application, create a PostgreSQL logical dump, copy `/data`, checksum the artifacts, encrypt the backup, copy it to the approved backup destination, and verify restoration in an isolated environment according to the recovery workflow/runbook.

A backup that has never been restored is not accepted as recovery evidence.

## Upgrade by digest

1. Confirm the target digest is exactly the artifact approved in release evidence.
2. Complete and verify the pre-upgrade backup.
3. Change only the intended immutable image reference(s) in the operator environment file.
4. Re-run the production deployment validator and inspect the rendered Compose model.
5. Pull the exact digests and record what Docker resolved.
6. Start the updated stack.
7. Wait for healthy state and run production smoke/client checks.
8. Record old/new digests, source SHA, PostgreSQL version/digest, UID/GID, time, operator, and result.

Never substitute another image merely because it shares a semantic version or source commit.

## Collect target-environment evidence

After the real target-environment rehearsal has completed—including backup creation, isolated restore rehearsal, rollback recording, reverse-proxy HTTPS/WSS validation, monitoring verification, log review, and the approved NetBird/private administrative-path check—use `scripts/collect-target-evidence.py` to capture the non-secret machine-observed state.

The collector is read-only. It validates the source contract, renders Compose, reads the restricted production environment file, inspects Docker metadata, and performs the canonical HTTPS health check. It does not deploy, restart, stop, remove, mutate, back up, restore, or reconfigure containers or infrastructure.

Example:

```bash
python3 scripts/collect-target-evidence.py \
  --env-file /etc/goreevault/production.env \
  --expected-manifest-digest "sha256:<64-hex RC manifest digest>" \
  --previous-known-good-image "ghcr.io/goreecloud/goreevault-server@sha256:<64-hex previous digest>" \
  --backup-reference "<approved backup reference>" \
  --rollback-reference "<approved rollback evidence reference>" \
  --reverse-proxy-https-wss \
  --backup-created \
  --restore-rehearsed \
  --rollback-recorded \
  --monitoring-verified \
  --logs-reviewed-for-sensitive-data \
  --netbird-path-verified \
  --output target-environment.json
```

Every manual flag is an operator attestation that the corresponding work actually occurred. Do not add a flag merely to make collection pass.

Review the output before copying it into `goreevault-stable-evidence.json`. The collector emits only the `target_environment` value and cannot approve the real-client, WebAuthn, Glaze UI, governance, or reviewer sections.

## Rollback

An older image digest is not automatically a safe rollback. If application storage may have changed incompatibly, stop the application and restore the exact pre-upgrade PostgreSQL dump plus `/data` backup into an isolated/replacement stack according to the tested recovery procedure.

Preserve failed deployment evidence until incident analysis is complete.

## Monitoring

At minimum monitor:

- container health and restart loops;
- GoreeVault `/alive` health;
- reverse-proxy TLS/certificate expiry;
- filesystem capacity for PostgreSQL, `/data`, and backups;
- backup completion and scheduled restore rehearsals;
- authentication/2FA anomalies and security-event retention;
- upstream Vaultwarden security releases and GoreeVault dependency/security alerts;
- unexpected changes to UID/GID, writable filesystems, capabilities, image digests, public binds, or registration/admin policy.

Monitoring labels and alerts must never contain vault contents, master passwords, tokens, TOTP seeds, recovery codes, session cookies, private keys, or unredacted database connection strings.
