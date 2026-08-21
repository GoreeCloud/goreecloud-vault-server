# GoreeCloud Vault Server — Glaze UI

## Purpose and authority

GoreeCloud Vault Server uses **Glaze UI** as the GoreeCloud visual and interaction language for every server presentation surface controlled by GoreeCloud. This repository-local contract applies the shared GoreeCloud Glaze UI Design Language, Application Branding and User Interface Design Standard, Privacy by Default, Code Structure and Documentation Standard, and mandatory software baseline without weakening the server's security or compatibility boundaries.

`GoreeVault` remains the broader client-family and historical product identity. GoreeVault Web, Browser, Desktop, Mobile, and the existing GoreeVault-family transactional-email boundary are not renamed by this server-identity change.

Security, accessibility, privacy, and operational comprehension take precedence over decoration.

Glaze UI compliance is a production-readiness gate, not an optional branding task.

## UI ownership boundary

GoreeCloud Vault Server currently has two presentation categories.

### GoreeCloud-controlled server surfaces

These must conform to Glaze UI now and use the canonical GoreeCloud Vault Server identity:

- server administration pages under `/admin`;
- server-rendered error/404 presentation;
- other server-owned presentation introduced in this repository in the future.

The shared transactional HTML and plain-text email templates remain an intentionally preserved **GoreeVault-family** presentation boundary because those messages serve the broader compatible client family. Their identity must not be silently renamed as a side effect of the server rename.

Transactional email uses an email-safe Glaze interpretation rather than browser-only effects. It must preserve GoreeVault family identity, readable hierarchy, restrained rounded/layered presentation where supported, system fonts, dark-mode hints where supported, local/no presentation tracking dependencies, and graceful degradation in older mail clients.

### Transitional compatibility surface

The bundled Bitwarden-compatible web vault is currently an upstream compatibility dependency. It exists to preserve supported-client interoperability while GoreeCloud establishes the native GoreeVault client path.

This is a **temporary development divergence**, not an approved permanent production exception. The existence of usable upstream styling, schedule pressure, or unfinished redesign work does not satisfy the GoreeCloud exception standard.

Under the current GoreeCloud baseline, Stable product readiness is blocked while the upstream-compatible web vault remains the primary browser vault unless one of the following becomes true:

1. GoreeVault Web replaces it and fully owns the browser presentation under Glaze UI; or
2. a separately approved material exception documents the exact Glaze requirement that cannot be met, the technical/legal/interoperability constraint, user-visible impact, compensating controls, approval, review/expiration condition, and removal condition.

No production Glaze UI exception is approved by this repository today.

## Source structure

The current server-owned presentation layer remains deliberately small and auditable:

- `src/static/templates/admin/base.hbs` — shared GoreeCloud Vault Server administration shell, identity, privacy metadata, navigation, appearance control, skip link, and main landmark.
- `src/static/scripts/admin.css` — Vault Server Admin Glaze tokens, layout, component presentation, accessibility fallbacks, and Bootstrap adaptation.
- `src/static/scripts/admin.js` — local System/Light/Dark appearance state plus existing same-origin admin behavior.
- `src/static/templates/404.hbs` — GoreeCloud Vault Server-owned error shell.
- `src/static/scripts/404.css` — Glaze presentation for the error shell.
- `src/static/templates/email/email_header.hbs` — shared GoreeVault-family HTML-email identity and email-safe Glaze shell.
- `src/static/templates/email/email_footer.hbs` — shared GoreeVault-family HTML-email footer.
- `src/static/templates/email/email_footer_text.hbs` — shared plain-text GoreeVault-family footer.
- `scripts/validate-glaze-ui.py` — source-level conformance checks.

Internal `vaultwarden` identifiers may remain where compatibility or upstream maintenance requires them. Rendered server-owned presentation must use the canonical GoreeCloud Vault Server identity. The shared transactional-email templates intentionally retain the GoreeVault-family identity until a separate client-family naming decision changes that boundary.

## Governing visual language

GoreeCloud-controlled presentation should be recognizable as GoreeCloud before a user studies the page. The Glaze signature includes:

- System/Light/Dark presentation where the platform supports it;
- layered surfaces with selective translucency;
- softened rounded geometry for navigation, cards, controls, forms, tables, and status elements;
- restrained shadows for hierarchy;
- purposeful GoreeCloud gradients that do not compete with security/operational content;
- consistent typography, spacing, radii, focus behavior, and semantic states;
- responsive layouts for desktop, laptop, tablet, and mobile;
- explicit textual status/error meaning rather than color-only meaning.

Glass effects are hierarchy tools, not a requirement on every element. If translucency reduces readability, use a solid surface. Email presentation must prefer broadly supported, degradable HTML/CSS over browser-only effects.

## GoreeCloud identity

Server-owned surfaces identify the product as **GoreeCloud Vault Server** or **Vault Server Admin** when the GoreeCloud context is already explicit. They must not render Vaultwarden or the retired **GoreeVault Server** name as the primary server interface identity.

Transactional emails intentionally identify the broader service family as **GoreeVault** and must not use the upstream Vaultwarden logo or an upstream project link as GoreeVault's product identity.

Browser presentation must use local repository-controlled assets only. Transactional email presentation must not require remote fonts, remote scripts, tracking pixels, remote branding images, analytics resources, or third-party design dependencies.

## Privacy metadata

Private/administrative GoreeCloud Vault Server pages declare:

- `robots=noindex,nofollow,noarchive`;
- `referrer=same-origin`;
- local-only scripts and styles.

These controls are defense in depth and do not replace authentication, authorization, NetBird/network policy, reverse-proxy controls, or HTTPS.

Transactional email does not have an equivalent browser indexing boundary; its privacy controls instead focus on avoiding remote tracking/presentation dependencies and minimizing sensitive information in message content and subject lines.

## Theme behavior

The default browser appearance is **System**, following `prefers-color-scheme`. The appearance selector provides:

1. System
2. Light
3. Dark

Only explicit Light or Dark choices are persisted. Returning to System removes the stored override.

The preference is stored only in browser `localStorage` under `goreecloud-goreevault-theme`. That compatibility-era key is intentionally retained to avoid unnecessary preference loss during the server rename. It is not sent to GoreeCloud Vault Server, stored in PostgreSQL, logged, used for analytics, or exposed to another service. Storage failure must not break the UI.

Transactional HTML email may declare light/dark color-scheme hints and dark-mode CSS where supported, but must remain readable when a mail client ignores those capabilities.

## Accessibility and interaction contract

GoreeCloud-controlled server browser presentation must preserve:

- semantic header/navigation/main landmarks;
- a keyboard-accessible skip link targeting a focusable main region;
- visible focus indicators;
- practical minimum 44-pixel interactive targets;
- readable contrast in System, Light, and Dark modes;
- keyboard operation for navigation, sign-in/admin controls, theme selection, and logout;
- reduced-motion behavior;
- stronger separation when `prefers-contrast: more` is requested;
- operable forced-colors/Windows High Contrast presentation;
- solid-surface fallback when backdrop filtering is unavailable;
- meaningful error/alert presentation with text, not color alone.

Motion is progressive enhancement. Hover motion is permitted only on hover-capable devices when reduced motion is not requested.

Email presentation must use real text for product identity and critical instructions, preserve readable text when images are blocked, avoid color-only meaning, and avoid making a decorative image necessary to understand the message.

## Privacy and dependency boundary

GoreeCloud-controlled server browser presentation must not introduce:

- remote fonts;
- remote JavaScript;
- remote stylesheets;
- analytics or behavioral tracking;
- telemetry SDKs;
- advertising resources;
- externally hosted icons or branding assets.

GoreeVault-family transactional email presentation must not introduce:

- tracking pixels;
- remote fonts or scripts;
- remotely hosted brand/logo images required for identity;
- analytics parameters solely for behavioral measurement;
- unnecessary upstream-project links presented as GoreeVault support or identity.

Normal user-activated external hyperlinks are not presentation dependencies, but GoreeCloud-controlled error/admin/email shells should avoid unnecessary upstream-brand links.

## Security boundary

Glaze changes presentation only. It must not weaken:

- zero-knowledge/client-side cryptographic behavior;
- authentication or authorization;
- CSRF or cookie protections;
- API compatibility;
- database migration semantics;
- attachment authorization;
- organization/collection authorization;
- audit/security logging boundaries;
- email token/action semantics;
- reverse-proxy, NetBird, or production network policy.

The administration interface remains disabled by default in the production deployment contract even though its presentation is Glaze-conformant.

## Automated conformance

Repository validation includes:

```bash
python3 scripts/validate-glaze-ui.py
python3 scripts/validate-repository-readiness.py
```

The Glaze checker verifies:

- canonical GoreeCloud Vault Server identity on server-owned admin/error presentation;
- noindex/noarchive and same-origin referrer metadata on owned browser shells;
- local-only browser presentation dependencies;
- skip-link/main-target semantics;
- System/Light/Dark local browser appearance behavior;
- the intentionally retained GoreeCloud-local compatibility theme-storage key;
- minimum target, focus, reduced-motion, increased-contrast, forced-colors, and backdrop-filter fallback rules;
- removal of user-facing Vaultwarden and retired GoreeVault Server branding from server-owned admin/error shells;
- GoreeVault-family identity in shared HTML/plain-text transactional email presentation;
- removal of the upstream Vaultwarden logo and upstream project link from shared email presentation;
- absence of remote/tracking presentation dependencies in the shared GoreeVault-family email shell.

The repository-readiness checker additionally prevents Stable documentation from silently treating the transitional upstream web vault as fully Glaze-conformant.

Automated source conformance does not replace real-browser or representative email-client visual/accessibility review.

## Release review boundary

Before a Stable release is visually approved, every GoreeCloud-controlled user-facing surface must satisfy the platform Glaze UI gate.

Material server-owned browser UI changes require authenticated review at representative desktop and mobile widths in System, Light, and Dark modes. Review must include keyboard-only navigation, reduced motion, increased contrast where available, forced colors where practical, authentication/admin errors, empty states, long values, tables/forms, and mobile navigation.

Material transactional email changes require representative rendering review in at least the supported/expected desktop and mobile mail-client families used by GoreeCloud, with images blocked and dark mode considered where practical. Security-sensitive action links and token semantics must be verified independently of styling.

The Stable evidence record must explicitly confirm product-wide Glaze UI conformance. An RC may continue to use the transitional upstream-compatible web vault for compatibility validation, but that does not authorize Stable product promotion under the current baseline.

The native GoreeVault Web, Browser, Desktop, and Mobile clients must adopt the same shared Glaze design language when they become GoreeCloud-owned products, while using platform-appropriate native accessibility and interaction conventions.
