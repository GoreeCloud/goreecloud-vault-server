# GoreeVault Web Browser Cutover Evidence

## Purpose

This directory defines the machine-readable evidence boundary for a future GoreeVault Web browser-client cutover.

The upstream-compatible bundled web vault remains the fallback browser client until GoreeVault Web satisfies the compatibility, security, accessibility, migration, recovery, and release requirements in `docs/WEB-CLIENT-CONTRACT.md`.

This tooling does not perform a production cutover and does not authorize Stable use.

## Evidence record

Start from `cutover-evidence.template.json`. A final record must identify:

- the previously accepted browser client, version, and artifact identity;
- the exact GoreeVault Web source revision;
- the immutable GoreeVault Web artifact SHA-256 identity;
- the matching release-manifest and SPDX SBOM SHA-256 identities;
- the exact GoreeVault Server source revision and OCI manifest digest;
- retained compatibility, accessibility, security, and rollback evidence references;
- the reviewed rollback procedure;
- the operator and timezone-aware timestamp;
- the terminal cutover outcome.

The rollback declaration must remain explicit that restoring the previously accepted browser presentation does not require a database downgrade or plaintext vault export.

## Validation

Validate the template structure during development:

```sh
python3 web-client/scripts/validate_cutover_evidence.py \
  web-client/migration/cutover-evidence.template.json \
  --allow-template
```

Validate a completed cutover record without `--allow-template`:

```sh
python3 web-client/scripts/validate_cutover_evidence.py /path/to/cutover-evidence.json
```

The final validator fails closed on placeholders, incomplete or unknown fields, malformed source/digest identities, timestamps without a timezone, non-terminal outcomes, database-downgrade rollback requirements, and plaintext-export rollback requirements.

## Sensitive-information boundary

Do not put passwords, master passwords, access tokens, refresh tokens, session cookies, private keys, TOTP seeds, recovery codes, decrypted vault contents, decrypted attachments, or reusable credentials in cutover evidence.

Evidence references should point to approved release or acceptance records rather than embedding private runtime data.
