# GoreeCloud Vault Server Capability Evidence

## Purpose

The Stable-evidence capability projector provides a minimized, machine-readable handoff from an exact-pinned GoreeCloud Vault Server candidate evidence bundle to a first-party capability consumer.

It is deliberately a companion to the canonical Stable evidence validator rather than a second validation authority.

## Validation dependency

Projection is allowed only after the canonical `scripts/validate-stable-evidence.py` logic accepts the supplied evidence using all three exact candidate expectations:

- source commit SHA;
- RC tag; and
- OCI manifest digest.

Missing or mismatched expected candidate identity fails closed. The projector does not loosen the Stable validator's requirements for real clients, multi-user isolation, WebAuthn, Glaze UI, target-environment evidence, governance, immutable artifacts, backup/rollback records, or final approval chronology.

## Minimized output

The projection identifies the bounded `vault.secrets` capability and selected candidate identity needed by a consumer. It does not expose vault contents, credentials, reusable secrets, reviewer identities, raw client evidence, backup references, rollback references, or the original evidence bundle.

## Production acceptance boundary

Successful Stable-evidence validation is evidence about the exact candidate bundle. It is not proof that a currently contacted runtime deployment is the accepted production deployment.

For that reason the current projection explicitly leaves runtime deployment unevaluated and emits `production_accepted: false`.

A future runtime acceptance path must be a separately reviewed integration that binds the contacted service to the accepted candidate and satisfies the applicable GoreeCloud Identity, Mesh, Privacy Shield, Wardveil Security, Everkeep, deployment, release, and operational authority boundaries.

## Security boundary

This projector does not modify credential handling, authorization, cryptography, persistence, WebAuthn, session state, or vault-data APIs. It is release/evidence tooling only.
