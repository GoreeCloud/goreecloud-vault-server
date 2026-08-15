# GoreeVault Security Scan Dispositions

GoreeVault blocks unsuppressed, fixed HIGH and CRITICAL vulnerabilities in both the repository/dependency scan and the built PostgreSQL production-image scan. Scanner or vulnerability-database execution failures fail closed.

This document records every temporary Trivy finding disposition in `.trivyignore.yaml` and resolved findings that materially shaped the production security model. An active exception is valid only while its evidence remains true and until its `expired_at` date. Expiration requires re-review; it must not be extended automatically.

## Why Vaultwarden package-version findings require code review

The inherited Cargo package metadata uses `name = "vaultwarden"` and `version = "1.0.0"`. That package version is not the upstream Vaultwarden release version represented by the GoreeVault baseline, so product-version vulnerability matching can report historical Vaultwarden advisories against newer source.

GoreeVault does not suppress such findings merely because the package version looks wrong. Each HIGH finding below was checked against the current source behavior that fixes the advisory.

## CVE-2024-55225 — auth-request user impersonation

**Disposition:** not affected by the historical vulnerable implementation; temporary scanner exception through 2026-09-30.

The advisory affects Vaultwarden before 1.32.5 and describes user impersonation through a crafted authorization request. Current GoreeVault password authentication resolves an auth request for the same user and rejects it unless all relevant binding checks pass, including:

- request belongs to the authenticating user
- request is approved
- request is not expired
- request IP matches
- access code matches

The current source therefore contains the upstream auth-request hardening rather than the historical vulnerable path.

Reopen this disposition immediately if auth-request lookup/binding logic changes.

## CVE-2026-27802 — bulk collection permission escalation

**Disposition:** fixed behavior present; temporary scanner exception through 2026-09-30.

The historical flaw allowed bulk collection access changes without revalidating management authority for each target collection. Current GoreeVault loads each target collection and calls `is_manageable_by_user` for the acting membership before modifying access.

Reopen this disposition immediately if bulk organization collection access logic or collection-management authorization changes.

## CVE-2026-27803 — collection Manager authorization

**Disposition:** fixed behavior present; temporary scanner exception through 2026-09-30.

The historical flaw treated collection visibility as sufficient for a Manager operation. Current GoreeVault `ManagerHeaders` checks `Collection::is_coll_manageable_by_user`, enforcing collection management authority rather than visibility alone.

Reopen this disposition immediately if `ManagerHeaders` or collection manageability semantics change.

## GHSA-82j2-j2ch-gfr8 — rustls-webpki CRL panic

**Disposition:** resolved; no active Trivy exception.

The original diagnostic found `rustls-webpki 0.101.7` through Rocket 0.5.1's optional embedded-TLS feature. GoreeVault production does not require Rocket to terminate public TLS: HTTPS/WSS terminate at the trusted reverse proxy and the application listener is HTTP-only on a private or loopback path.

GoreeVault therefore disabled Rocket's `tls` feature instead of retaining a reachability-based vulnerability exception. The lockfile was regenerated under CI and its approved SHA-256 was verified before commit. The resulting PostgreSQL dependency graph contains the modern rustls branch and no longer contains the legacy Rocket TLS packages that introduced `rustls-webpki 0.101.7`.

The permanent security workflow rejects reintroduction of Rocket embedded TLS and the legacy dependency family. Reopen this disposition if the application is ever expected to terminate TLS directly, if the Rocket dependency declaration changes, or if an upstream merge attempts to restore the old TLS branch.

This remediation does **not** weaken the external transport requirement. Every client connection must still use HTTPS/WSS. Direct public access to the HTTP application listener is forbidden.

## Built-image diagnostic result

The split diagnostic rehearsal built the real PostgreSQL production image and separately reported image findings. The image annotations contained lower-severity/unknown Debian package findings but no HIGH or CRITICAL image findings. The previous workflow still marked the image step as a failure because vulnerability exit status and scanner execution status were conflated.

The corrected GoreeVault security workflow therefore:

1. enforces the production TLS dependency boundary before vulnerability scanning;
2. runs Trivy with vulnerability exit code `0`, so a non-success action outcome represents scanner/runtime failure rather than policy findings;
3. limits SARIF to HIGH/CRITICAL severity;
4. applies the reviewed `.trivyignore.yaml` file;
5. uploads and annotates SARIF;
6. fails closed when the scanner outcome is not successful or expected SARIF is missing; and
7. independently fails when filtered SARIF contains any unsuppressed fixed HIGH/CRITICAL result.

This preserves fail-closed scanner behavior while making the release policy deterministic and auditable.

## Review rules for exceptions

Every vulnerability exception must:

- name one exact vulnerability/advisory ID;
- include a written technical statement;
- have an expiration date;
- be covered by GoreeCloud CODEOWNERS;
- be backed by current source/reachability evidence;
- be removed when the underlying package/source condition changes; and
- be revalidated before any Stable release if the evidence predates the candidate source commit.

Blanket package, directory, severity, or scanner exceptions are not accepted for Stable release evidence.
