# GoreeCloud Vault Server Security Policy

GoreeCloud Vault Server handles authentication material and encrypted vault data. Security reports must be treated as sensitive even when the suspected issue appears minor.

GoreeCloud Vault Server is currently derived from Vaultwarden. We retain and respect the upstream project's security work, but GoreeCloud-specific server vulnerabilities should be reported to GoreeCloud first so we can determine whether the issue comes from our changes, upstream code, or their interaction.

`GoreeVault` remains the broader client-family and historical product identity; server-specific security records use the canonical GoreeCloud Vault Server name defined in `docs/SERVER-IDENTITY.md`.

## Supported status

GoreeCloud Vault Server is pre-1.0 development software. A branch, source commit, passing CI run, or release-candidate image must not be treated as Stable production authorization by itself.

Stable promotion requires the exact-artifact security, compatibility, migration/rollback, backup/restore, deployment, governance, real-client, multi-user, and Glaze UI gates defined in `docs/PRODUCTION-READINESS.md`.

## Reporting a GoreeCloud Vault Server vulnerability

Do not publish exploit details, credentials, private vault data, tokens, database dumps, backups, session material, TOTP seeds, recovery codes, or other sensitive material in a public GitHub issue, pull request, discussion, social-media post, or other public channel.

Use GitHub's private vulnerability reporting feature for this repository when it is available.

If GitHub private vulnerability reporting is unavailable, send the report privately to:

**security@goreecloud.com**

Use a clear subject such as `GoreeCloud Vault Server security report`. Do not send production vault exports, production databases, reusable credentials, or more private user data than is necessary to explain the issue.

The GoreeCloud public responsible-security-reporting policy is also published at `https://www.goreecloud.com/security.html`.

This repository has ordinary GitHub Issues disabled, so a public issue is **not** the security-reporting fallback.

A useful private report includes:

- affected GoreeCloud Vault Server commit or release;
- affected component and deployment mode;
- reproducible steps using synthetic data;
- expected and observed behavior;
- security impact;
- suggested mitigation, if known.

Please allow a reasonable period for investigation and remediation before public disclosure, and make a good-faith effort to avoid privacy violations, destruction of data, denial of service, spam, or social engineering while researching.

## GoreeCloud Vault Server security boundaries

The server must treat vault ciphertext as opaque. Clients perform vault encryption/decryption; server-side changes must not introduce plaintext inspection or master-password storage.

Changes that alter authentication, cryptography, key handling, refresh/session tokens, attachment authorization, organization/collection authorization, migrations, backup/restore, deployment trust boundaries, or release workflows require dedicated regression testing and security review.

Password refresh-token consumption is expected to be single-use and atomic under concurrency. Replay/concurrency protections must remain covered by compatibility tests.

Real production secrets and production GoreeCloud vault data must never be added to tests, fixtures, issues, pull requests, CI logs, workflow artifacts, or repository history.

## Production network and runtime boundary

Production clients connect to `https://vault.goreecloud.com`. HTTPS/WSS terminates at the trusted GoreeCloud reverse proxy. The GoreeCloud Vault Server application listener remains HTTP-only behind that trust boundary and must never be directly exposed to the public network.

Production policy requires:

- loopback-only backend publication;
- PostgreSQL with no host-published database port;
- immutable GoreeCloud Vault Server and PostgreSQL image digests;
- non-root steady-state application execution;
- read-only application root filesystem;
- all application Linux capabilities dropped;
- `no-new-privileges`;
- public registration closed by default;
- `/admin` disabled by default;
- verified backup/restore and migration/rollback evidence before promotion.

See `docs/PRODUCTION-DEPLOYMENT.md` and `docs/PRODUCTION-READINESS.md`.

## Glaze UI security boundary

GoreeCloud-controlled presentation follows `docs/GLAZE-UI.md`. Glaze is a presentation and interaction standard; it must not weaken authentication, authorization, cryptography, CSRF/cookie protections, network policy, email action semantics, or client/API compatibility.

GoreeCloud-owned browser surfaces must remain self-contained and privacy-preserving: no remote fonts, scripts, stylesheets, analytics, advertising, behavioral tracking, telemetry SDKs, or externally hosted branding assets.

GoreeVault-family transactional email presentation must avoid remote tracking pixels, remote fonts/scripts, unnecessary upstream branding links, and remotely hosted brand images required for identity.

The bundled upstream-compatible web vault is currently a transitional compatibility asset and does not establish product-wide GoreeVault Glaze ownership.

## Release governance

A fixed HIGH/CRITICAL vulnerability, expired/broad security exception, missing exact-head gate, unprotected release path, or unverified production trust boundary blocks Stable promotion.

Repository governance controls are part of the security boundary. Until `main` is protected and a reviewer-gated `release` GitHub environment exists and is verified, GoreeCloud Vault Server must remain non-Stable regardless of source test results.

## Upstream Vaultwarden vulnerabilities

If a vulnerability is confirmed to exist unchanged in upstream Vaultwarden, we will coordinate responsibly and avoid publishing details that would expose upstream users before a fix is available. Upstream security contacts and disclosure guidance remain authoritative for vulnerabilities in upstream Vaultwarden itself.

GoreeCloud Vault Server must evaluate relevant upstream security fixes promptly. GoreeCloud-specific changes must not silently block, weaken, or delay an upstream security fix.

`docs/UPSTREAM.md` defines the maintained-fork review process and records point-in-time upstream audits.

## Out of scope

The following are generally outside the GoreeCloud Vault Server security-reporting scope unless GoreeCloud-specific behavior materially changes the impact:

- vulnerabilities already fixed in the current GoreeCloud Vault Server candidate;
- vulnerabilities solely in Bitwarden clients, the upstream web vault, Rust, operating systems, or unrelated third-party software;
- attacks requiring physical access to a user's device without a GoreeCloud-specific weakness;
- missing best practices that do not directly create a security vulnerability;
- denial-of-service testing, spam, phishing, or social engineering.

Normal reliability, hardening, documentation, Glaze UI, and best-practice improvements remain welcome through reviewed GoreeCloud Vault Server pull requests and the appropriate GoreeCloud project workflow.
