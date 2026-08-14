#!/usr/bin/env python3
from pathlib import Path

path = Path("src/db/models/device.rs")
text = path.read_text(encoding="utf-8")
old = '''        let updated = conn
            .run(move |conn| {
                diesel::update(devices::table)
                    .filter(devices::uuid.eq(uuid))
                    .filter(devices::user_uuid.eq(user_uuid))
                    .filter(devices::refresh_token.eq(expected_refresh_token))
                    .set((devices::refresh_token.eq(new_refresh_token_for_update), devices::updated_at.eq(updated_at)))
                    .execute(conn)
                    .map_res("Error consuming device refresh token")
            })
            .await?;
'''
new = '''        let updated = conn
            .run(move |conn| {
                let result = diesel::update(devices::table)
                    .filter(devices::uuid.eq(uuid))
                    .filter(devices::user_uuid.eq(user_uuid))
                    .filter(devices::refresh_token.eq(expected_refresh_token))
                    .set((devices::refresh_token.eq(new_refresh_token_for_update), devices::updated_at.eq(updated_at)))
                    .execute(conn);
                <Result<usize, diesel::result::Error> as MapResult<usize>>::map_res(
                    result,
                    "Error consuming device refresh token",
                )
            })
            .await?;
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one CAS row-count target, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
