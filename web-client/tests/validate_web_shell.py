#!/usr/bin/env python3
"""Fail-closed source validation for the GoreeVault Web incubation shell."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def validate_html() -> None:
    html = read("index.html")
    required = [
        'data-glaze-ui',
        'name="robots" content="noindex,nofollow,noarchive"',
        'name="referrer" content="same-origin"',
        'http-equiv="Content-Security-Policy"',
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        'href="#main">Skip to vault workspace</a>',
        'id="main" tabindex="-1"',
        'id="appearance-toggle"',
        'aria-live="polite"',
        'Local shell only · no credential processing',
        'Authentication, encryption, sync, and real vault data remain intentionally disabled',
    ]
    missing = [token for token in required if token not in html]
    require(not missing, f"index.html is missing required shell contract tokens: {missing}")

    for remote in re.findall(r'(?:src|href)="(https?://[^"]+)"', html):
        raise ValueError(f"remote presentation dependency is not allowed: {remote}")

    csp_match = re.search(r'Content-Security-Policy" content="([^"]+)"', html)
    require(csp_match is not None, "CSP metadata is required")
    csp = csp_match.group(1)
    require("unsafe-eval" not in csp, "CSP must not allow unsafe-eval")
    require("unsafe-inline" not in csp, "CSP must not allow unsafe-inline")


def validate_css() -> None:
    css = read("assets/glaze.css")
    required = [
        "backdrop-filter",
        "border-radius",
        "prefers-reduced-motion: reduce",
        "prefers-contrast: more",
        "forced-colors: active",
        "prefers-reduced-transparency: reduce",
        ":focus-visible",
        "min-height: 44px",
        'data-appearance="light"',
        'data-appearance="dark"',
    ]
    missing = [token for token in required if token not in css]
    require(not missing, f"Glaze UI stylesheet is missing accessibility/design tokens: {missing}")
    require("@import url(" not in css.lower(), "remote CSS imports are not allowed")


def validate_javascript() -> None:
    theme = read("assets/theme-init.js")
    app = read("assets/app.js")
    combined = theme + "\n" + app
    require("goreevault-web-appearance" in combined, "appearance preference key is required")
    require("system" in combined and "light" in combined and "dark" in combined, "System/Light/Dark modes are required")
    forbidden = [
        "console.log(",
        "console.debug(",
        "fetch('http",
        'fetch("http',
        "google-analytics",
        "gtag(",
        "segment.com",
        "mixpanel",
    ]
    found = [token for token in forbidden if token in combined.lower()]
    require(not found, f"forbidden browser telemetry/debug surface found: {found}")


def validate_security_docs() -> None:
    readme = read("README.md")
    security = read("docs/SECURITY-BOUNDARY.md")
    require("not approved for production use" in readme, "README must preserve pre-production state")
    require("must move to its own GoreeCloud-owned repository" in readme, "standalone repository requirement must remain explicit")
    require("Do not invent cryptographic primitives" in security, "security boundary must prohibit invented cryptography")
    require("must not be used with real vault credentials" in security, "pre-alpha real-credential prohibition is required")
    require("plaintext vault" in security, "plaintext storage prohibition must be documented")


def validate_svg() -> None:
    svg = read("assets/goreevault-mark.svg")
    require("<script" not in svg.lower(), "identity SVG must be script-free")
    require("http://www.w3.org/2000/svg" in svg, "identity asset must be a local SVG")


def main() -> int:
    try:
        for path in [
            "README.md",
            "index.html",
            "assets/glaze.css",
            "assets/theme-init.js",
            "assets/app.js",
            "assets/goreevault-mark.svg",
            "docs/SECURITY-BOUNDARY.md",
        ]:
            require((ROOT / path).is_file(), f"missing required web shell file: {path}")
        validate_html()
        validate_css()
        validate_javascript()
        validate_security_docs()
        validate_svg()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"GoreeVault Web shell validation failed: {exc}", file=sys.stderr)
        return 1

    print("GoreeVault Web Glaze UI shell validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
