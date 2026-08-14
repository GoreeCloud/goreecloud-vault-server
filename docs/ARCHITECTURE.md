# GoreeVault Architecture — v0.1.0

## Objective

Establish a GoreeCloud-owned password-manager platform while preserving a mature Bitwarden-compatible protocol foundation during the transition.

## Runtime

```text
Bitwarden-compatible clients
          |
          | HTTPS / WSS
          v
reverse proxy / TLS
          |
          v
GoreeVault Server
(Vaultwarden-derived compatibility core)
          |
          +-------------------+
          |                   |
          v                   v
PostgreSQL              persistent /data
metadata + encrypted    keys, attachments,
vault records           sends, runtime files
```

## Trust boundary

The public application endpoint is `https://vault.goreecloud.com`. Infrastructure administration should be reachable only from GoreeCloud administrative network paths (for example a private NetBird policy) rather than exposed as a generally reachable public management surface.

## v0.1.0 invariants

1. Keep Bitwarden-compatible API routes unchanged.
2. Keep cryptographic behavior unchanged.
3. Keep database migrations and model names unchanged.
4. Keep the Rust package/binary named `vaultwarden` internally for now.
5. Apply GoreeVault branding only to product-facing/admin text and GoreeVault-owned documentation/deployment files.
6. Use PostgreSQL for the GoreeCloud development/production target.
7. No production Vaultwarden data migration until restore and compatibility tests exist.

## Future component boundaries

```text
GoreeVault Web       GoreeVault Browser       GoreeVault Desktop
      \                    |                       /
       +---------------- GoreeVault Client SDK ---+
                              |
                     client-side crypto
                              |
                       GoreeVault API
                              |
                         PostgreSQL
```

The long-term goal is progressively GoreeCloud-owned clients and server components, not a permanent cosmetic fork.
