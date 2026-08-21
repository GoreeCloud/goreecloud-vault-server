#!/usr/bin/env python3
"""Serve the GoreeVault Argon2id browser harness over loopback-only HTTPS.

Validation only. This server exposes only reviewed harness/candidate files, adds
strict browser headers, and refuses non-loopback binds. It is not a production
web server and does not authorize credential processing or provider registration.
"""

from __future__ import annotations

import argparse
import http.server
import ipaddress
import mimetypes
import os
import ssl
from pathlib import Path
from urllib.parse import unquote, urlsplit

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8443
ALLOWED_FILES = frozenset({
    "argon2id-real-browser-harness.html",
    "argon2id-real-browser-harness.js",
    "goreevault_web_argon2id_core.js",
    "goreevault_web_argon2id_core_bg.wasm",
})
CSP = (
    "default-src 'none'; script-src 'self'; connect-src 'self'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'"
)


def require_loopback(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("Validation server host must be a literal loopback IP address.") from exc
    if not address.is_loopback:
        raise ValueError("Validation server may bind only to a loopback address.")
    return host


def safe_candidate_path(root: Path, request_path: str) -> Path:
    path = unquote(urlsplit(request_path).path)
    name = "argon2id-real-browser-harness.html" if path in {"", "/"} else path.removeprefix("/")
    if "/" in name or "\\" in name or name not in ALLOWED_FILES:
        raise FileNotFoundError(name)
    candidate = root / name
    if candidate.is_symlink() or not candidate.is_file():
        raise FileNotFoundError(name)
    return candidate


class HarnessHandler(http.server.BaseHTTPRequestHandler):
    server_version = "GoreeVaultValidation/1"

    def do_GET(self) -> None:  # noqa: N802
        root = Path(self.server.candidate_root)  # type: ignore[attr-defined]
        try:
            target = safe_candidate_path(root, self.path)
        except FileNotFoundError:
            self.send_error(404)
            return

        data = target.read_bytes()
        content_type = "application/wasm" if target.suffix == ".wasm" else (mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        # Avoid logging request targets/query strings that could contain operator data.
        print(f"{self.address_string()} - request completed")


def build_server(candidate_root: Path, host: str, port: int, cert: Path, key: Path):
    require_loopback(host)
    root = candidate_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Candidate root must be a directory.")
    if cert.is_symlink() or key.is_symlink():
        raise ValueError("TLS certificate and key paths must not be symbolic links.")
    if not cert.is_file() or not key.is_file():
        raise ValueError("TLS certificate and key files are required.")
    if port < 1024 or port > 65535:
        raise ValueError("Validation port must be between 1024 and 65535.")

    server = http.server.ThreadingHTTPServer((host, port), HarnessHandler)
    server.candidate_root = os.fspath(root)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=cert, keyfile=key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_root", type=Path)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=DEFAULT_PORT, type=int)
    parser.add_argument("--cert", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    args = parser.parse_args()

    server = build_server(args.candidate_root, args.host, args.port, args.cert, args.key)
    print(f"Serving validation harness at https://{args.host}:{args.port}/")
    print("Validation only: do not enter a real master password or production account data.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
