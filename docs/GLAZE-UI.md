# GoreeVault — Glaze UI

## Purpose and authority

GoreeVault uses **Glaze UI** as the GoreeCloud visual and interaction language for every presentation surface owned by GoreeVault. This repository-local contract applies the shared GoreeCloud Glaze UI Design Language, Application Branding and User Interface Design Standard, Privacy by Default, and Code Structure and Documentation Standard without weakening GoreeVault's security or compatibility boundaries.

Security, accessibility, privacy, and operational comprehension take precedence over decoration.

## UI ownership boundary

GoreeVault currently has two presentation categories:

### GoreeVault-owned surfaces

These must conform to Glaze UI now:

- server administration pages under `/admin`;
- server-rendered error/404 presentation;
- GoreeVault-native presentation introduced in this repository in the future.

### Compatibility-owned surface

The bundled Bitwarden-compatible web vault is currently an upstream compatibility asset. It remains intentionally protocol/client compatible and is not yet a GoreeVault-native presentation layer.

GoreeVault must not describe the entire product as fully Glaze-conformant while that upstream web-vault surface remains in use. The complete product-wide Glaze claim becomes valid only when GoreeVault Web replaces or fully owns that presentation layer without breaking the approved compatibility contract.

## Source structure

The current server-owned presentation layer remains deliberately small and auditable:

- `src/static/templates/admin/base.hbs` — shared GoreeVault administration shell, identity, privacy metadata, navigation, appearance control, skip link, and main landmark.
- `src/static/scripts/admin.css` — GoreeVault Admin Glaze tokens, layout, component presentation, accessibility fallbacks, and Bootstrap adaptation.
- `src/static/scripts/admin.js` — local System/Light/Dark appearance state plus existing same-origin admin behavior.
- `src/static/templates/404.hbs` — GoreeVault-owned error shell.
- `src/static/scripts/404.css` — Glaze presentation for the error shell.
- `scripts/validate-glaze-ui.py` — source-level conformance checks.

Internal `vaultwarden` identifiers may remain where compatibility or upstream maintenance requires them. Rendered GoreeVault-owned UI must use GoreeVault product identity.

## Governing visual language

GoreeVault should be recognizable as GoreeCloud before a user studies the page. The Glaze signature includes:

- dark-first, high-quality System/Light/Dark presentation;
- layered surfaces with selective translucency;
- softened rounded geometry for navigation, cards, controls, forms, tables, and status elements;
- restrained shadows for hierarchy;
- purposeful GoreeCloud gradients that do not compete with security/operational content;
- consistent typography, spacing, radii, focus behavior, and semantic states;
- responsive layouts for desktop, laptop, tablet, and mobile;
- explicit textual status/error meaning rather than color-only meaning.

Glass effects are hierarchy tools, not a requirement on every element. If translucency reduces readability, use a solid surface.

## GoreeCloud identity

GoreeVault-owned surfaces identify the product as **GoreeVault** or **GoreeVault Admin**. They must not render Vaultwarden product branding as the primary interface identity.

The browser presentation must use local repository-controlled assets only. No remote logo, icon set, font, analytics package, design CDN, or third-party presentation service is required for GoreeVault-owned surfaces.

## Privacy metadata

Private/administrative GoreeVault pages declare:

- `robots=noindex,nofollow,noarchive`;
- `referrer=same-origin`;
- local-only scripts and styles.

These controls are defense in depth and do not replace authentication, authorization, NetBird/network policy, reverse-proxy controls, or HTTPS.

## Theme behavior

The default appearance is **System**, following `prefers-color-scheme`. The appearance selector provides:

1. System
2. Light
3. Dark

Only explicit Light or Dark choices are persisted. Returning to System removes the stored override.

The preference is stored only in browser `localStorage` under `goreecloud-goreevault-theme`. It is not sent to GoreeVault, stored in PostgreSQL, logged, used for analytics, or exposed to another service. Storage failure must not break the UI.

## Accessibility and interaction contract

GoreeVault-owned presentation must preserve:

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

## Privacy and dependency boundary

GoreeVault-owned browser presentation must not introduce:

- remote fonts;
- remote JavaScript;
- remote stylesheets;
- analytics or behavioral tracking;
- telemetry SDKs;
- advertising resources;
- externally hosted icons or branding assets.

Normal user-activated external hyperlinks are not presentation dependencies, but GoreeVault-owned error/admin shells should avoid unnecessary upstream-brand links.

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
- reverse-proxy, NetBird, or production network policy.

The administration interface remains disabled by default in the production deployment contract even though its presentation is Glaze-conformant.

## Automated conformance

Repository validation includes:

```bash
python3 scripts/validate-glaze-ui.py
```

The checker verifies the GoreeVault-owned shell for:

- GoreeVault identity;
- noindex/noarchive and same-origin referrer metadata;
- local-only browser presentation dependencies;
- skip-link/main-target semantics;
- System/Light/Dark local appearance behavior;
- GoreeCloud-local theme storage key;
- minimum target, focus, reduced-motion, increased-contrast, forced-colors, and backdrop-filter fallback rules;
- removal of user-facing Vaultwarden branding from GoreeVault-owned admin/error shells.

Automated source conformance does not replace real-browser visual/accessibility review.

## Release review boundary

Before a Stable release is visually approved, material GoreeVault-owned UI changes require authenticated browser review at representative desktop and mobile widths in System, Light, and Dark modes. Review must include keyboard-only navigation, reduced motion, increased contrast where available, forced colors where practical, authentication/admin errors, empty states, long values, tables/forms, and mobile navigation.

The native GoreeVault Web, Browser, Desktop, and Mobile clients must adopt the same shared Glaze design language when they become GoreeVault-owned products, while using platform-appropriate native accessibility and interaction conventions.
