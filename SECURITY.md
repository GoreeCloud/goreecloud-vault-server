# GoreeVault Security Policy

GoreeVault handles authentication material and encrypted vault data. Security reports should therefore be treated as sensitive even when the suspected issue appears minor.

GoreeVault is currently derived from Vaultwarden. We retain and respect the upstream project's security work, but GoreeVault-specific vulnerabilities should be reported to GoreeVault first so we can determine whether the issue comes from our changes, upstream code, or their interaction.

## Supported status

GoreeVault is currently pre-1.0 development software. No GoreeVault release should be treated as production-ready until the roadmap's migration, rollback, backup/restore, compatibility, and security gates are complete.

## Reporting a GoreeVault vulnerability

Do not publish exploit details, credentials, private vault data, tokens, database dumps, or other sensitive material in a public GitHub issue.

Use GitHub's private vulnerability reporting feature for this repository when available. If private reporting is unavailable, open a minimal public issue stating only that you need a private security contact; do not include exploit details in that issue.

A useful private report includes:

- affected GoreeVault commit or release
- affected component and deployment mode
- reproducible steps using synthetic data
- expected and observed behavior
- security impact
- suggested mitigation, if known

Please allow a reasonable period for investigation and remediation before public disclosure, and make a good-faith effort to avoid privacy violations, destruction of data, denial of service, spam, or social engineering while researching.

## GoreeVault security boundaries

The GoreeVault server must treat vault ciphertext as opaque. Changes that alter authentication, cryptography, key handling, token issuance, attachment authorization, organization authorization, migrations, or backup/restore behavior require dedicated regression testing and security review.

Real production secrets and production GoreeCloud vault data must never be added to tests, fixtures, issues, pull requests, CI logs, or repository history.

## Upstream Vaultwarden vulnerabilities

If a vulnerability is confirmed to exist unchanged in upstream Vaultwarden, we will coordinate responsibly and avoid publishing details that would expose upstream users before a fix is available. Upstream security contacts and disclosure guidance remain authoritative for vulnerabilities in upstream Vaultwarden itself.

GoreeVault must also evaluate relevant upstream security fixes promptly. GoreeVault-specific changes must not silently block, weaken, or delay an upstream security fix.

## Out of scope

The following are generally outside the GoreeVault security-reporting scope unless GoreeVault-specific behavior materially changes the impact:

- vulnerabilities already fixed in the current GoreeVault branch
- vulnerabilities solely in Bitwarden clients, web-vault, Rust, operating systems, or unrelated third-party software
- attacks requiring physical access to a user's device without a GoreeVault-specific weakness
- missing best practices that do not directly create a security vulnerability
- denial-of-service testing, spam, phishing, or social engineering

Normal reliability, hardening, documentation, and best-practice improvements are still welcome through ordinary issues or pull requests.
