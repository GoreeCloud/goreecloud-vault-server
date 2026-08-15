# GoreeVault Client Compatibility Evidence

This document is the release-evidence record for real Bitwarden-compatible client testing. Automated API tests do not replace this matrix.

Create one completed copy or dated section for each GoreeVault release candidate. Do not mark a client class supported from memory or from an older server build.

## Release candidate under test

- GoreeVault tag:
- Source commit SHA:
- OCI image digest:
- Test start date/time and timezone:
- Tester:
- Test environment/domain:
- PostgreSQL version:
- Notes/known limitations:

Every row below must be run against the **same source commit and release image digest** recorded above. If the server changes, start a new matrix.

## Result vocabulary

Use only:

- `PASS` — exercised successfully on this RC
- `FAIL` — exercised and failed; include a failure reference/note
- `N/A` — feature is genuinely unavailable for that client/platform; explain why
- `NOT TESTED` — no evidence yet; this blocks Stable when the row is required

## Web vault

- Browser/version:
- OS/version:

| Test | Result | Notes |
|---|---|---|
| Login | NOT TESTED | |
| Lock/unlock | NOT TESTED | |
| Vault sync | NOT TESTED | |
| Create/read/update/delete cipher | NOT TESTED | |
| Attachment upload/download/delete | NOT TESTED | |
| TOTP login | NOT TESTED | |
| Organization collection access | NOT TESTED | |
| Organization access revocation after membership removal | NOT TESTED | |

## Chromium-family extension

- Browser/version:
- Extension/version:
- OS/version:

| Test | Result | Notes |
|---|---|---|
| Login/unlock | NOT TESTED | |
| Vault sync | NOT TESTED | |
| Autofill | NOT TESTED | |
| Create/update item | NOT TESTED | |
| TOTP login | NOT TESTED | |

## Firefox extension

- Firefox version:
- Extension version:
- OS/version:

| Test | Result | Notes |
|---|---|---|
| Login/unlock | NOT TESTED | |
| Vault sync | NOT TESTED | |
| Autofill | NOT TESTED | |
| Create/update item | NOT TESTED | |
| TOTP login | NOT TESTED | |

## Desktop client

- Client/version:
- OS/version:

| Test | Result | Notes |
|---|---|---|
| Login/unlock | NOT TESTED | |
| Vault sync | NOT TESTED | |
| Create/update item | NOT TESTED | |
| Attachment access where supported | NOT TESTED | |
| TOTP login | NOT TESTED | |

## Android client

- Bitwarden-compatible client/version:
- Android version/device class:

| Test | Result | Notes |
|---|---|---|
| Login/unlock | NOT TESTED | |
| Vault sync | NOT TESTED | |
| Autofill | NOT TESTED | |
| Create/update item | NOT TESTED | |
| Attachment access where supported | NOT TESTED | |
| TOTP login | NOT TESTED | |

## CLI

- CLI/version:
- OS/version:

| Test | Result | Notes |
|---|---|---|
| Login | NOT TESTED | |
| Sync/list/get | NOT TESTED | |
| Create/edit where supported | NOT TESTED | |
| Logout/session invalidation | NOT TESTED | |

## Real WebAuthn/passkey evidence

At least one successful registration and authentication path must use an actual supported authenticator. The automated malformed-attestation/challenge test is not sufficient for this section.

- Browser/client and exact version:
- OS/version:
- Authenticator type/model or platform authenticator:
- RP/domain tested:

| Test | Result | Notes |
|---|---|---|
| Register real WebAuthn/passkey credential | NOT TESTED | |
| Lock/logout and authenticate with registered credential | NOT TESTED | |
| Normal vault sync after WebAuthn authentication | NOT TESTED | |
| Remove credential and verify it can no longer authenticate | NOT TESTED | |

Do not record private keys, recovery codes, TOTP seeds, attestation secrets, passwords, or other credentials in this file.

## Failure references

For every `FAIL`, record enough non-secret information to reproduce and triage it:

- client and exact version
- operation that failed
- expected behavior
- observed behavior/error class
- relevant GoreeVault CI/log reference with secrets removed
- disposition: release blocker / accepted limitation / client unsupported

## RC sign-off

- All required rows are `PASS` or justified `N/A`: NO
- Real WebAuthn/passkey evidence is `PASS`: NO
- No unresolved client-compatibility release blockers: NO
- Tested image digest matches the candidate being promoted: NO
- Final reviewer/date:

A `NO`, `FAIL`, or required `NOT TESTED` entry keeps the candidate below Stable maturity.
