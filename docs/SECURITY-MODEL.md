# GoreeVault Security Model — v0.1.0

## Security posture

GoreeVault v0.1.0 is intentionally conservative. It changes ownership and product surface before it changes security-critical implementation.

## Protected assets

- encrypted vault items
- account encryption metadata
- authentication/session material
- TOTP secrets stored inside encrypted vault items
- passkey and WebAuthn-related records
- SSH/private-key items stored by clients in encrypted vault data
- attachments and Sends
- server RSA/private keys
- database credentials
- administrator credentials
- backups

## Rules

- Never log plaintext vault item content or secrets.
- Never store master passwords.
- Never add server-side plaintext inspection of vault contents.
- Never commit production secrets or `.env` files.
- Keep admin access private where operationally possible.
- Use HTTPS for every client connection.
- Treat backups as sensitive security material.
- Restore testing is part of backup correctness.
- Dependency and upstream changes require review before production promotion.

## v0.1.0 cryptographic scope

No cryptographic primitives are replaced in v0.1.0. This includes encryption, key derivation, Argon2 processing, JWT/token signing, WebAuthn behavior and client-side vault cryptography assumptions.

## Development environment rule

Use a fresh database and non-production credentials. Do not point v0.1.0 development builds at the current production Vaultwarden data directory or database.
