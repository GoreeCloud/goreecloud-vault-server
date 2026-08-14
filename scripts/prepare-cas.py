#!/usr/bin/env python3
"""Prepare the atomic password refresh-token consume patch on a scratch branch.

This helper is intentionally strict: every source replacement must match
exactly once or the preparation workflow aborts without committing anything.
"""

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one patch target, found {count}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "src/db/models/device.rs",
    '''    pub async fn find_by_refresh_token(refresh_token: &str, conn: &DbConn) -> Option<Self> {
        conn.run(move |conn| devices::table.filter(devices::refresh_token.eq(refresh_token)).first::<Self>(conn).ok())
            .await
    }

    pub async fn find_latest_active_by_user(user_uuid: &UserId, conn: &DbConn) -> Option<Self> {
''',
    '''    pub async fn find_by_refresh_token(refresh_token: &str, conn: &DbConn) -> Option<Self> {
        conn.run(move |conn| devices::table.filter(devices::refresh_token.eq(refresh_token)).first::<Self>(conn).ok())
            .await
    }

    pub async fn rotate_refresh_token_if_matches(
        &mut self,
        expected_refresh_token: &str,
        conn: &DbConn,
    ) -> Result<bool, crate::error::Error> {
        let uuid = self.uuid.clone();
        let user_uuid = self.user_uuid.clone();
        let expected_refresh_token = expected_refresh_token.to_owned();
        let new_refresh_token = Self::generate_refresh_token();
        let new_refresh_token_for_update = new_refresh_token.clone();
        let updated_at = Utc::now().naive_utc();

        let updated = conn
            .run(move |conn| {
                diesel::update(devices::table)
                    .filter(devices::uuid.eq(uuid))
                    .filter(devices::user_uuid.eq(user_uuid))
                    .filter(devices::refresh_token.eq(expected_refresh_token))
                    .set((
                        devices::refresh_token.eq(new_refresh_token_for_update),
                        devices::updated_at.eq(updated_at),
                    ))
                    .execute(conn)
                    .map_res("Error consuming device refresh token")
            })
            .await?;

        if updated == 1 {
            self.refresh_token = new_refresh_token;
            self.updated_at = updated_at;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub async fn find_latest_active_by_user(user_uuid: &UserId, conn: &DbConn) -> Option<Self> {
''',
)

replace_once(
    "src/auth.rs",
    '''    // Save to update `updated_at`.
    device.save(true, conn).await?;

    let Some(user) = User::find_by_uuid(&device.user_uuid, conn).await else {
''',
    '''    // SSO refresh semantics are unchanged. Password refresh updates the
    // device timestamp as part of its atomic refresh-secret consumption below.
    if matches!(&refresh_claims.sub, AuthMethod::Sso) {
        device.save(true, conn).await?;
    }

    let Some(user) = User::find_by_uuid(&device.user_uuid, conn).await else {
''',
)

replace_once(
    "src/auth.rs",
    '''        AuthMethod::Password => {
            // Password refresh tokens are single-use. Rotate the server-side
            // device secret before minting the next refresh JWT so replaying
            // the prior JWT cannot find a matching device token.
            device.refresh_token = Device::generate_refresh_token();
            device.save(false, conn).await?;
            AuthTokens::new(&device, &user, refresh_claims.sub, client_id)
        }
''',
    '''        AuthMethod::Password => {
            // Consume the password refresh secret atomically. If another
            // request already rotated this device from the same JWT, this
            // conditional update affects zero rows and the replay loses.
            if !device.rotate_refresh_token_if_matches(&refresh_claims.device_token, conn).await? {
                err!("Invalid refresh token")
            }
            AuthTokens::new(&device, &user, refresh_claims.sub, client_id)
        }
''',
)

replace_once(
    "tests/compat/compat.py",
    '''import argparse
import json
import sys
import time
''',
    '''import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import sys
import threading
import time
''',
)

replace_once(
    "tests/compat/compat.py",
    '''def sync(token: str) -> dict[str, Any]:
''',
    '''def concurrent_refresh_single_winner() -> None:
    _access, original_refresh = login()
    workers = 16
    barrier = threading.Barrier(workers)

    def attempt_refresh(_: int) -> Response:
        barrier.wait(timeout=10)
        return request(
            "POST",
            "/identity/connect/token",
            form={
                "grant_type": "refresh_token",
                "client_id": "web",
                "refresh_token": original_refresh,
            },
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        responses = list(pool.map(attempt_refresh, range(workers)))

    successes = [resp for resp in responses if 200 <= resp.status < 300]
    failures = [resp for resp in responses if not (200 <= resp.status < 300)]
    require(len(successes) == 1, f"concurrent refresh expected one winner, got {len(successes)}")
    require(len(failures) == workers - 1, f"concurrent refresh expected {workers - 1} losers, got {len(failures)}")

    for resp in failures:
        require(resp.status == 400, f"concurrent refresh loser returned HTTP {resp.status}: {resp.text()}")
        body = resp.json()
        require(
            isinstance(body, dict) and body.get("error") == "invalid_grant",
            f"concurrent refresh loser was not invalid_grant: {resp.text()}",
        )

    winner_body = successes[0].json()
    require(isinstance(winner_body, dict), "concurrent refresh winner did not return an object")
    winner_refresh = winner_body.get("refresh_token")
    require(isinstance(winner_refresh, str) and winner_refresh, "concurrent refresh winner omitted refresh_token")
    require(winner_refresh != original_refresh, "concurrent refresh winner did not rotate refresh token")

    _winner_access, successor_refresh = refresh_login(winner_refresh)
    require(successor_refresh != winner_refresh, "winner refresh token was not consumable exactly once")
    refresh_replay_rejected(original_refresh)
    print("PASS  concurrent refresh-token consume has exactly one winner")


def sync(token: str) -> dict[str, Any]:
''',
)

replace_once(
    "tests/compat/compat.py",
    '''    access, _new_refresh = refresh_login(refresh)
    refresh_replay_rejected(refresh)

    register_account(
''',
    '''    access, _new_refresh = refresh_login(refresh)
    refresh_replay_rejected(refresh)
    concurrent_refresh_single_winner()

    register_account(
''',
)
