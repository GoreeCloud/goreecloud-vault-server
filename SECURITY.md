# GoreeVault Security Policy

GoreeVault handles authentication material and encrypted vault data. Security reports must be treated as sensitive even when the suspected issue appears minor.

GoreeVault is currently derived from Vaultwarden. We retain and respect the upstream project's security work, but GoreeVault-specific vulnerabilities should be reported to GoreeVault first so we can determine whether the issue comes from our changes, upstream code, or their interaction.

## Supported status

GoreeVault is pre-1.0 development software. A branch, source commit, passing CI run, or release-candidate image must not be treated as Stable production authorization by itself.

Stable promotion requires the exact-artifact security, compatibility, migration/rollback, backup/restore, deployment, governance, real-client, and Glaze UI gates defined in `docs/PRODUCTION-READINESS.md`.

## Reporting a GoreeVault vulnerability

Do not publish exploit details, credentials, private vault data, tokens, database dumps, backups, session material, TOTP seeds, recovery codes, or other sensitive material in a public GitHub issue.

Use GitHub's private vulnerability reporting feature for this repository when available. If private reporting is unavailable, open a minimal public issue stating only that you need a private security contact; do not include exploit details in that issue.

A useful private report includes:

- affected GoreeVault commit or release;
- affected component and deployment mode;
- reproducible steps using synthetic data;
- expected and observed behavior;
- security impact;
- suggested mitigation, if known.

Please allow a reasonable period for investigation and remediation before public disclosure, and make a good-faith effort to avoid privacy violations, destruction of data, denial of service, spam, or social engineering while researching.

## GoreeVault security boundaries

The GoreeVault server must treat vault ciphertext as opaque. Clients perform vault encryption/decryption; server-side changes must not introduce plaintext inspection or master-password storage.

Changes that alter authentication, cryptography, key handling, refresh/session tokens, attachment authorization, organization/collection authorization, migrations, backup/restore, deployment trust boundaries, or release workflows require dedicated regression testing and security review.

Password refresh-token consumption is expected to be single-use and atomic under concurrency. Replay/concurrency protections must remain covered by compatibility tests.

Real production secrets and production GoreeCloud vault data must never be added to tests, fixtures, issues, pull requests, CI logs, workflow artifacts, or repository history.

## Production network and runtime boundary

Production clients connect to `https://vault.goreecloud.com`. HTTPS/WSS terminates at the trusted GoreeCloud reverse proxy. The GoreeVault application listener remains HTTP-only behind that trust boundary and must never be directly exposed to the public network.

Production policy requires:

- loopback-only backend publication;
- PostgreSQL with no host-published database port;
- immutable GoreeVault and PostgreSQL image digests;
- non-root steady-state application execution;
- read-only application root filesystem;
- all application Linux capabilities dropped;
- `no-new-privileges`;
- public registration closed by default;
- `/admin` disabled by default;
- verified backup/restore and migration/rollback evidence before promotion.

See `docs/PRODUCTION-DEPLOYMENT.md` and `docs/PRODUCTION-READINESS.md`.

## Glaze UI security boundary

GoreeVault-owned presentation follows `docs/GLAZE-UI.md`. Glaze is a presentation and interaction standard; it must not weaken authentication, authorization, cryptography, CSRF/cookie protections, network policy, or client/API compatibility.

GoreeVault-owned browser surfaces must remain self-contained and privacy-preserving: no remote fonts, scripts, stylesheets, analytics, advertising, behavioral tracking, telemetry SDKs, or externally hosted branding assets.

The bundled upstream-compatible web vault is currently a transitional compatibility asset and does not establish product-wide GoreeVault Glaze ownership.

## Release governance

A fixed HIGH/CRITICAL vulnerability, expired/broad security exception, missing exact-head gate, unprotected release path, or unverified production trust boundary blocks Stable promotion.

Repository governance controls are part of the security boundary. Until `main` is protected and a reviewer-gated `release` GitHub environment exists and is verified, GoreeVault must remain non-Stable regardless of source test results.

## Upstream Vaultwarden vulnerabilities

If a vulnerability is confirmed to exist unchanged in upstream Vaultwarden, we will coordinate responsibly and avoid publishing details that would expose upstream users before a fix is available. Upstream security contacts and disclosure guidance remain authoritative for vulnerabilities in upstream Vaultwarden itself.

GoreeVault must evaluate relevant upstream security fixes promptly. GoreeVault-specific changes must not silently block, weaken, or delay an upstream security fix.

## Out of scope

The following are generally outside the GoreeVault security-reporting scope unless GoreeVault-specific behavior materially changes the impact:

- vulnerabilities already fixed in the current GoreeVault candidate;
- vulnerabilities solely in Bitwarden clients, the upstream web vault, Rust, operating systems, or unrelated third-party software;
- attacks requiring physical access to a user's device without a GoreeVault-specific weakness;
- missing best practices that do not directly create a security vulnerability;
- denial-of-service testing, spam, phishing, or social engineering.

Normal reliability, hardening, documentation, Glaze UI, and best-practice improvements remain welcome through ordinary issues or pull requests.
