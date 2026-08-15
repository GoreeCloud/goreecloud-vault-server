#!/usr/bin/env python3
"""Source-level GoreeVault Glaze UI conformance checks.

This checker validates GoreeVault-owned browser and transactional-email
presentation surfaces. The bundled Bitwarden-compatible web vault remains a
transitional compatibility asset until GoreeVault Web owns that presentation
layer.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ADMIN_BASE = ROOT / "src/static/templates/admin/base.hbs"
ADMIN_LOGIN = ROOT / "src/static/templates/admin/login.hbs"
ADMIN_JS = ROOT / "src/static/scripts/admin.js"
ADMIN_CSS = ROOT / "src/static/scripts/admin.css"
ERROR_TEMPLATE = ROOT / "src/static/templates/404.hbs"
ERROR_CSS = ROOT / "src/static/scripts/404.css"
EMAIL_HEADER = ROOT / "src/static/templates/email/email_header.hbs"
EMAIL_FOOTER = ROOT / "src/static/templates/email/email_footer.hbs"
EMAIL_FOOTER_TEXT = ROOT / "src/static/templates/email/email_footer_text.hbs"
GLAZE_DOC = ROOT / "docs/GLAZE-UI.md"
READINESS_DOC = ROOT / "docs/PRODUCTION-READINESS.md"

FILES = [
    ADMIN_BASE,
    ADMIN_LOGIN,
    ADMIN_JS,
    ADMIN_CSS,
    ERROR_TEMPLATE,
    ERROR_CSS,
    EMAIL_HEADER,
    EMAIL_FOOTER,
    EMAIL_FOOTER_TEXT,
    GLAZE_DOC,
    READINESS_DOC,
]


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required Glaze UI file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing required contract {needle!r}")


def reject(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: forbidden presentation text/dependency {needle!r}")


def validate_local_browser_dependencies(template: str, css: str, label: str) -> None:
    remote_script = re.compile(r"<script\b[^>]*\bsrc=[\"']https?://", re.I)
    remote_style = re.compile(
        r"<link\b[^>]*\brel=[\"'][^\"']*stylesheet[^\"']*[\"'][^>]*\bhref=[\"']https?://",
        re.I,
    )
    remote_style_reversed = re.compile(
        r"<link\b[^>]*\bhref=[\"']https?://[^\"']+[\"'][^>]*\brel=[\"'][^\"']*stylesheet",
        re.I,
    )
    css_import = re.compile(r"@import\s+(?:url\()?\s*[\"']?https?://", re.I)
    css_url = re.compile(r"url\(\s*[\"']?https?://", re.I)

    for pattern, description, source in (
        (remote_script, "remote script dependency", template),
        (remote_style, "remote stylesheet dependency", template),
        (remote_style_reversed, "remote stylesheet dependency", template),
        (css_import, "remote CSS import", css),
        (css_url, "remote CSS asset", css),
    ):
        if pattern.search(source):
            raise AssertionError(f"{label}: {description} is forbidden by GoreeCloud Privacy by Default")


def validate_email_dependencies(email_html: str) -> None:
    remote_script = re.compile(r"<script\b", re.I)
    tracking_image = re.compile(r"<img\b[^>]*\bsrc=[\"']https?://", re.I)
    remote_font = re.compile(r"(?:@import|url\()[^\n]*https?://", re.I)

    for pattern, description in (
        (remote_script, "script dependency"),
        (tracking_image, "remote image/tracking dependency"),
        (remote_font, "remote CSS/font dependency"),
    ):
        if pattern.search(email_html):
            raise AssertionError(f"GoreeVault email: {description} is forbidden by GoreeCloud Privacy by Default")


def main() -> None:
    for path in FILES:
        if not path.is_file():
            raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")

    admin_base = read(ADMIN_BASE)
    admin_login = read(ADMIN_LOGIN)
    admin_js = read(ADMIN_JS)
    admin_css = read(ADMIN_CSS)
    error_template = read(ERROR_TEMPLATE)
    error_css = read(ERROR_CSS)
    email_header = read(EMAIL_HEADER)
    email_footer = read(EMAIL_FOOTER)
    email_footer_text = read(EMAIL_FOOTER_TEXT)
    glaze_doc = read(GLAZE_DOC)
    readiness = read(READINESS_DOC)

    # GoreeVault identity and privacy metadata on owned browser surfaces.
    require(admin_base, "GoreeVault Admin", "admin shell identity")
    require(admin_base, 'content="noindex,nofollow,noarchive"', "admin robots policy")
    require(admin_base, 'content="same-origin"', "admin referrer policy")
    require(admin_base, 'href="#gv-main"', "admin skip link")
    require(admin_base, 'data-bs-theme-value="system"', "admin System appearance")
    require(admin_base, 'data-bs-theme-value="light"', "admin Light appearance")
    require(admin_base, 'data-bs-theme-value="dark"', "admin Dark appearance")

    # The private Admin sign-in path must not regress to placeholder-only input.
    require(admin_login, "Sign in to GoreeVault Admin", "admin sign-in identity")
    require(admin_login, 'for="gv-admin-token"', "admin token visible label")
    require(admin_login, 'id="gv-admin-token"', "admin token label target")
    require(admin_login, 'autocomplete="current-password"', "admin token autocomplete semantics")
    require(admin_login, "required", "admin token required state")
    require(admin_login, 'aria-describedby="gv-admin-token-help"', "admin token help association")
    require(admin_login, 'role="alert"', "admin sign-in error semantics")
    require(admin_login, 'aria-live="polite"', "admin sign-in live error semantics")

    require(error_template, "GoreeVault", "404 GoreeVault identity")
    require(error_template, 'content="noindex,nofollow,noarchive"', "404 robots policy")
    require(error_template, 'content="same-origin"', "404 referrer policy")
    require(error_template, 'id="gv-main"', "404 main target")
    require(error_template, 'tabindex="-1"', "404 focusable main target")
    require(error_template, 'href="#gv-main"', "404 skip link")

    # Product-facing legacy branding must not survive on GoreeVault-owned shells.
    for owned_text, label in (
        (admin_base, "admin shell"),
        (admin_login, "admin sign-in"),
        (error_template, "404 shell"),
    ):
        reject(owned_text, "Vaultwarden Admin", label)
        reject(owned_text, ">Vaultwarden<", label)
        reject(owned_text, "vaultwarden-icon.png", label)
        reject(owned_text, "vaultwarden-favicon.png", label)
        reject(owned_text, "github.com/dani-garcia/vaultwarden", label)

    # GoreeVault-owned transactional email must use GoreeVault identity without
    # requiring upstream branding or remote presentation/tracking resources.
    require(email_header, "<title>GoreeVault</title>", "email document identity")
    require(email_header, ">GoreeVault</div>", "email visible GoreeVault identity")
    require(email_header, "GoreeCloud secure vault", "email GoreeCloud relationship")
    require(email_header, 'content="light dark"', "email color-scheme hint")
    require(email_footer, "GoreeVault", "email footer identity")
    require(email_footer, "GoreeCloud self-hosted credential platform", "email footer role")
    require(email_footer_text, "GoreeVault · GoreeCloud", "plain-text email identity")
    for email_text, label in (
        (email_header, "email header"),
        (email_footer, "email footer"),
        (email_footer_text, "plain-text email footer"),
    ):
        reject(email_text, "Vaultwarden", label)
        reject(email_text, "github.com/dani-garcia/vaultwarden", label)
    reject(email_header, "logo-gray.png", "email upstream logo asset")
    validate_email_dependencies(email_header + email_footer)

    # Browser-local, privacy-preserving appearance contract.
    require(admin_js, 'THEME_STORAGE_KEY = "goreecloud-goreevault-theme"', "GoreeCloud theme storage key")
    require(admin_js, 'new Set(["system", "light", "dark"])', "allowed appearance modes")
    require(admin_js, 'removeItem(THEME_STORAGE_KEY)', "System removes appearance override")
    require(admin_js, 'matchMedia("(prefers-color-scheme: dark)")', "System color-scheme support")
    require(admin_js, 'main.id = "gv-main"', "admin main skip target")
    require(admin_js, 'main.setAttribute("tabindex", "-1")', "admin focusable main target")

    # Cross-cutting Glaze accessibility and resilience requirements.
    for css, label in ((admin_css, "admin CSS"), (error_css, "404 CSS")):
        require(css, "min-block-size: 2.75rem", f"{label} minimum interactive target")
        require(css, ":focus-visible", f"{label} focus visibility")
        require(css, "prefers-reduced-motion", f"{label} reduced-motion support")
        require(css, "prefers-contrast: more", f"{label} increased-contrast support")
        require(css, "forced-colors: active", f"{label} forced-colors support")
        require(css, "@supports not (backdrop-filter", f"{label} no-blur fallback")

    # GoreeCloud presentation assets must be local. User-activated links are not
    # dependencies; this checks scripts/styles/CSS imports/assets only.
    validate_local_browser_dependencies(admin_base + admin_login, admin_css, "GoreeVault Admin")
    validate_local_browser_dependencies(error_template, error_css, "GoreeVault 404")

    # Governance docs must state the stricter transitional ownership boundary,
    # reject a silent production exception, and preserve the Stable blocker.
    require(glaze_doc, "GoreeVault-owned surfaces", "Glaze ownership boundary")
    require(glaze_doc, "transactional HTML and plain-text email", "transactional email ownership boundary")
    require(glaze_doc, "Transitional compatibility surface", "web-vault transitional boundary")
    require(glaze_doc, "temporary development divergence", "temporary web-vault divergence")
    require(
        glaze_doc,
        "No production Glaze UI exception is approved",
        "Glaze production-exception boundary",
    )
    require(
        glaze_doc,
        "Stable product readiness is blocked",
        "product-wide Glaze Stable blocker",
    )
    require(
        readiness,
        "A green source build is necessary but is not production authorization",
        "release evidence boundary",
    )
    require(readiness, "Known repository-state blocker", "manual governance blockers")
    require(readiness, "Stable is therefore blocked", "product-wide Glaze release blocker")

    print("GoreeVault Glaze UI source conformance validated.")


if __name__ == "__main__":
    main()
