# GoreeVault Client Compatibility Evidence

This document is the release-evidence record for **real client testing** against an exact GoreeVault Release Candidate. Automated API tests do not replace this matrix.

Create one completed copy or dated section for each GoreeVault RC. Do not mark a client class supported from memory, from an older server build, or from a different OCI manifest.

This matrix is aligned to Stable-evidence schema version 2. Each required client section contains the exact machine-readable check keys consumed by `scripts/validate-stable-evidence.py` so the human test record and final `goreevault-stable-evidence.json` cannot silently diverge.

## Release candidate under test

- GoreeVault tag:
- Source commit SHA:
- GoreeVault OCI manifest digest:
- PostgreSQL image and immutable digest:
- Browser-vault asset/client name, version, and immutable identity:
- Test start date/time and timezone:
- Test completion date/time and timezone:
- Tester:
- Test environment/domain:
- Notes/known limitations:

Every required row below must be run against the **same source commit and release image digest** recorded above. If the server, browser-vault artifact, or release manifest changes, begin a new matrix unless the applicable release policy explicitly establishes an immutable equivalent artifact identity.

## Result vocabulary

Use only:

- `PASS` — exercised successfully on this exact RC with retained non-secret evidence;
- `FAIL` — exercised and failed; include a failure reference/note;
- `N/A` — feature is genuinely unavailable for that client/platform; explain why;
- `NOT TESTED` — no evidence yet.

### Stable promotion rule

Stable-evidence schema version 2 currently requires **all eight machine-readable checks to be true for every required client kind**. Therefore `N/A`, `FAIL`, and `NOT TESTED` do **not** satisfy the current Stable client gate even when `N/A` accurately describes an upstream client limitation.

If a required client genuinely cannot exercise a schema-required capability, do not convert `N/A` to `PASS`. Treat the mismatch as a release-contract issue: either the client is not supportable under the current Stable matrix or the Stable evidence schema must be deliberately reviewed and changed in a separate release-policy change.

## Evidence handling rules

For every `PASS`, retain enough non-secret information to identify what was tested without storing private user data or reusable credentials. Evidence may reference screenshots, test notes, CI artifacts, isolated synthetic test records, or approved logs after secret review.

Never record or attach:

- master passwords;
- plaintext vault item values;
- TOTP seeds;
- recovery codes;
- passkey/private-key material;
- bearer or refresh tokens;
- session cookies;
- database credentials;
- decrypted attachments;
- private production-user information.

Use synthetic test identities and synthetic vault content wherever practical.

## Required Stable client checks

Every required client kind must provide these exact Stable-evidence keys:

| Stable evidence key | Required behavior |
|---|---|
| `sign_in_unlock` | Sign in successfully and reach an unlocked usable vault state. |
| `full_sync` | Complete a full vault synchronization and observe expected synthetic data. |
| `create_update_delete` | Create, read/observe, update, and delete supported synthetic vault data. |
| `attachments` | Exercise the supported attachment lifecycle required by the release contract. |
| `organization_collections` | Verify authorized organization/collection access and relevant authorization changes. |
| `totp` | Complete the supported TOTP authentication/workflow required by the release contract. |
| `refresh_rotation_replay` | Prove session refresh rotation and replay rejection using an approved non-secret test method tied to the real client session. |
| `logout_session_invalidation` | Log out or revoke the applicable session/device and prove the old session can no longer be used. |

The `refresh_rotation_replay` row may require an approved developer/network-test harness around a real client session because normal client UI does not expose refresh tokens. Do not record the token itself. The evidence must prove behavior without preserving the reusable credential.

## Web client — `kind: web`

- Client name:
- Exact client/browser-vault version or immutable asset identity:
- Browser/version:
- OS/version:
- Tested at and timezone:

| Test | Stable evidence key | Result | Evidence / notes |
|---|---|---|---|
| Sign in and unlock | `sign_in_unlock` | NOT TESTED | |
| Full vault sync | `full_sync` | NOT TESTED | |
| Create/read/update/delete synthetic item | `create_update_delete` | NOT TESTED | |
| Attachment upload/download/delete | `attachments` | NOT TESTED | |
| Organization/collection access and authorization change | `organization_collections` | NOT TESTED | |
| TOTP workflow | `totp` | NOT TESTED | |
| Refresh rotation and replay rejection | `refresh_rotation_replay` | NOT TESTED | |
| Logout/session invalidation | `logout_session_invalidation` | NOT TESTED | |

## Chromium-family extension — `kind: chromium_extension`

- Client name:
- Browser/version:
- Extension/version:
- OS/version:
- Tested at and timezone:

| Test | Stable evidence key | Result | Evidence / notes |
|---|---|---|---|
| Sign in and unlock | `sign_in_unlock` | NOT TESTED | |
| Full vault sync | `full_sync` | NOT TESTED | |
| Create/update/delete synthetic item | `create_update_delete` | NOT TESTED | |
| Attachment lifecycle required by Stable contract | `attachments` | NOT TESTED | |
| Organization/collection behavior and authorization change | `organization_collections` | NOT TESTED | |
| TOTP workflow | `totp` | NOT TESTED | |
| Refresh rotation and replay rejection | `refresh_rotation_replay` | NOT TESTED | |
| Logout/session invalidation | `logout_session_invalidation` | NOT TESTED | |
| Autofill on approved synthetic test origin | — supplemental | NOT TESTED | |
| Capture/update credential from approved synthetic test origin | — supplemental | NOT TESTED | |

## Firefox extension — `kind: firefox_extension`

- Client name:
- Firefox version:
- Extension version:
- OS/version:
- Tested at and timezone:

| Test | Stable evidence key | Result | Evidence / notes |
|---|---|---|---|
| Sign in and unlock | `sign_in_unlock` | NOT TESTED | |
| Full vault sync | `full_sync` | NOT TESTED | |
| Create/update/delete synthetic item | `create_update_delete` | NOT TESTED | |
| Attachment lifecycle required by Stable contract | `attachments` | NOT TESTED | |
| Organization/collection behavior and authorization change | `organization_collections` | NOT TESTED | |
| TOTP workflow | `totp` | NOT TESTED | |
| Refresh rotation and replay rejection | `refresh_rotation_replay` | NOT TESTED | |
| Logout/session invalidation | `logout_session_invalidation` | NOT TESTED | |
| Autofill on approved synthetic test origin | — supplemental | NOT TESTED | |
| Capture/update credential from approved synthetic test origin | — supplemental | NOT TESTED | |

## Desktop client — `kind: desktop`

- Client name/version:
- OS/version:
- Tested at and timezone:

| Test | Stable evidence key | Result | Evidence / notes |
|---|---|---|---|
| Sign in and unlock | `sign_in_unlock` | NOT TESTED | |
| Full vault sync | `full_sync` | NOT TESTED | |
| Create/update/delete synthetic item | `create_update_delete` | NOT TESTED | |
| Attachment lifecycle required by Stable contract | `attachments` | NOT TESTED | |
| Organization/collection behavior and authorization change | `organization_collections` | NOT TESTED | |
| TOTP workflow | `totp` | NOT TESTED | |
| Refresh rotation and replay rejection | `refresh_rotation_replay` | NOT TESTED | |
| Logout/session invalidation | `logout_session_invalidation` | NOT TESTED | |

## Android client — `kind: android`

- Client name/version:
- Android version/device class:
- Tested at and timezone:

| Test | Stable evidence key | Result | Evidence / notes |
|---|---|---|---|
| Sign in and unlock | `sign_in_unlock` | NOT TESTED | |
| Full vault sync | `full_sync` | NOT TESTED | |
| Create/update/delete synthetic item | `create_update_delete` | NOT TESTED | |
| Attachment lifecycle required by Stable contract | `attachments` | NOT TESTED | |
| Organization/collection behavior and authorization change | `organization_collections` | NOT TESTED | |
| TOTP workflow | `totp` | NOT TESTED | |
| Refresh rotation and replay rejection | `refresh_rotation_replay` | NOT TESTED | |
| Logout/session invalidation | `logout_session_invalidation` | NOT TESTED | |
| Android autofill on approved synthetic test origin/application | — supplemental | NOT TESTED | |
| Background/lock recovery behavior | — supplemental | NOT TESTED | |

## CLI — `kind: cli`

- Client name/version:
- OS/version:
- Tested at and timezone:

| Test | Stable evidence key | Result | Evidence / notes |
|---|---|---|---|
| Sign in and unlock | `sign_in_unlock` | NOT TESTED | |
| Full sync/list/get expected synthetic data | `full_sync` | NOT TESTED | |
| Create/update/delete supported synthetic item | `create_update_delete` | NOT TESTED | |
| Attachment lifecycle required by Stable contract | `attachments` | NOT TESTED | |
| Organization/collection behavior and authorization change | `organization_collections` | NOT TESTED | |
| TOTP workflow | `totp` | NOT TESTED | |
| Refresh rotation and replay rejection | `refresh_rotation_replay` | NOT TESTED | |
| Logout/session invalidation | `logout_session_invalidation` | NOT TESTED | |

## Real WebAuthn/passkey evidence

Stable evidence also requires one real supported browser/device/authenticator path. The automated malformed-attestation/challenge coverage is not sufficient.

Record:

- Browser/client name and exact version:
- OS/device version:
- Authenticator type/model or platform authenticator:
- RP/domain tested:
- Tested at and timezone:

| Test | Stable evidence field | Result | Evidence / notes |
|---|---|---|---|
| Register a real WebAuthn/passkey credential | `webauthn.registration` | NOT TESTED | |
| Authenticate using the registered credential | `webauthn.authentication` | NOT TESTED | |
| Lock/logout and reauthenticate as applicable | supplemental | NOT TESTED | |
| Normal vault sync after WebAuthn authentication | supplemental | NOT TESTED | |
| Remove/revoke credential and verify expected denial | supplemental | NOT TESTED | |

For Stable, both `webauthn.registration` and `webauthn.authentication` must be `PASS` and the exact browser, browser version, platform, authenticator, and offset-aware test timestamp must be transferred to the final evidence record.

## Cross-user authorization observation

The separate `multi_user` Stable evidence section remains authoritative for multi-user readiness. During real-client testing, capture non-secret observations that support that section where applicable:

- unrelated User A cannot view User B private vault data;
- organization membership grants only expected shared access;
- collection authorization is enforced;
- permission changes take effect after sync/reauthentication as appropriate;
- member removal removes shared access;
- session/device invalidation takes effect;
- no shared administrator identity is required for ordinary users.

Do not duplicate private vault contents into this record.

## Failure references

For every `FAIL`, record enough non-secret information to reproduce and triage it:

- client kind, name, and exact version;
- platform/OS/browser version;
- exact Stable evidence key or supplemental operation that failed;
- expected behavior;
- observed behavior/error class;
- relevant GoreeVault CI/log/test reference after secret review;
- disposition: release blocker / accepted non-Stable limitation / client unsupported.

An accepted limitation does not override a schema-required Stable `true` field.

## Transfer to `goreevault-stable-evidence.json`

For each required client:

1. copy the exact client `kind`, name, platform, and version;
2. use an offset-aware `tested_at` timestamp;
3. set `result` to `pass` only when every schema-required row is `PASS`;
4. map each table row to its exact `checks` key;
5. do not infer `true` from an untested or supplemental behavior;
6. validate the completed full evidence file with `scripts/validate-stable-evidence.py`.

The final Stable evidence file, not this Markdown record, is what the release workflow machine-validates. This record exists to make that final file auditable rather than hand-authored from memory.

## RC sign-off

- Web `kind` has all eight schema-required checks `PASS`: NO
- Chromium extension `kind` has all eight schema-required checks `PASS`: NO
- Firefox extension `kind` has all eight schema-required checks `PASS`: NO
- Desktop `kind` has all eight schema-required checks `PASS`: NO
- Android `kind` has all eight schema-required checks `PASS`: NO
- CLI `kind` has all eight schema-required checks `PASS`: NO
- Real WebAuthn `registration` and `authentication` are `PASS`: NO
- No unresolved required client-compatibility release blockers: NO
- Tested source SHA and OCI manifest exactly match the candidate being promoted: NO
- Browser-vault asset identity exactly matches the candidate being promoted: NO
- Final reviewer/date/timezone:

Any `NO`, required `FAIL`, required `N/A`, or required `NOT TESTED` entry keeps the candidate below Stable maturity under schema version 2.
