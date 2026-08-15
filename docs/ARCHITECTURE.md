# GoreeVault Architecture — v0.1.0

## Objective

Establish a GoreeCloud-owned password-manager platform while preserving a mature Bitwarden-compatible protocol foundation during the transition.

## Runtime

```text
Bitwarden-compatible clients
          |
          | HTTPS / WSS
          v
trusted reverse proxy / TLS
          |
          | private or loopback HTTP
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

## Trust boundaries

The public application endpoint is `https://vault.goreecloud.com`.

### External transport boundary

The trusted GoreeCloud reverse proxy is the only component allowed to terminate public HTTPS/WSS for the production service. GoreeVault's Rocket application listener is intentionally HTTP-only and does not enable Rocket's embedded TLS feature.

The HTTP application listener is therefore an **internal transport**, not a public endpoint. It must be reachable only from the trusted reverse proxy over one of these deployment patterns:

- host loopback, such as the development/host-proxy bind `127.0.0.1:8080:80`; or
- an isolated private container/VM network reachable by the reverse proxy but not by untrusted clients.

Binding the GoreeVault application port to `0.0.0.0` on a public host interface, directly forwarding it through a firewall/NAT rule, or otherwise exposing the HTTP listener to untrusted networks is forbidden.

Disabling Rocket embedded TLS reduces the application dependency and attack surface; it does **not** relax the requirement that every client connection use HTTPS/WSS.

### Administrative boundary

Infrastructure administration should be reachable only from GoreeCloud administrative network paths, such as a private NetBird policy, rather than exposed as a generally reachable public management surface. The GoreeVault application endpoint and infrastructure-management plane are separate trust boundaries.

## v0.1.0 invariants

1. Keep Bitwarden-compatible API routes unchanged.
2. Keep cryptographic behavior unchanged.
3. Keep database migrations and model names unchanged.
4. Keep the Rust package/binary named `vaultwarden` internally for now.
5. Apply GoreeVault branding only to product-facing/admin text and GoreeVault-owned documentation/deployment files.
6. Use PostgreSQL for the GoreeCloud development/production target.
7. Public client traffic terminates HTTPS/WSS at the trusted reverse proxy; the GoreeVault application listener is never directly public.
8. Keep Rocket default features disabled and do not enable Rocket's embedded `tls` feature in the production dependency graph.
9. No production Vaultwarden data migration until restore and compatibility tests exist.

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
