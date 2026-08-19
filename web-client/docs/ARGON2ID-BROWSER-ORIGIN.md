# GoreeVault Web Argon2id Validation Origin

## Purpose

The real-browser Argon2id harness must run from a controlled HTTPS origin. `web-client/scripts/serve_argon2id_browser_harness.py` provides a validation-only server for that purpose.

## Security boundary

The server binds only to a literal loopback address such as `127.0.0.1` or `::1`. It refuses wildcard, LAN, hostname, and public bind targets. It serves only the reviewed harness HTML/JavaScript and exact generated Argon2id JavaScript/WebAssembly candidate filenames from the selected candidate directory.

The server rejects symbolic-link candidate files, requires an explicit TLS certificate and key, uses TLS 1.2 or newer, emits `Cache-Control: no-store`, and applies a restrictive Content Security Policy with same-origin script and connection loading. It does not provide directory listing, uploads, form handlers, credential storage, authentication, production publication, or provider approval.

## Operator use

Generate or obtain a locally trusted validation certificate outside this repository. Do not commit certificate private keys. Prepare a candidate directory containing exactly the harness files and the generated candidate artifacts, then run:

```text
python3 web-client/scripts/serve_argon2id_browser_harness.py <candidate-dir> --cert <certificate.pem> --key <private-key.pem>
```

Open `https://127.0.0.1:8443/` in the supported browser being evaluated. The browser must trust the validation certificate without bypassing certificate warnings. Do not enter a real master password, production account identifier, real two-factor token, or production vault data.

## Evidence relationship

The server establishes a reproducible HTTPS and CSP boundary only. A successful server start does not prove that a browser ran, that WebAssembly initialized, that interoperability passed, or that memory/performance behavior is acceptable. The resulting browser run must still be reviewed and retained under `ARGON2ID-REAL-BROWSER-EVIDENCE.md` and pass `validate_browser_argon2id_evidence.py`.

Credential processing, production release inclusion, provider registration, RC promotion, and Stable promotion remain separate approvals.
