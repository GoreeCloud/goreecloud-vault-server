#!/usr/bin/env python3
"""GoreeVault destructive backup/restore verification fixture.

This test treats encrypted vault fields and attachment bytes as opaque client
ciphertext. It seeds a fresh instance, records stable object identifiers, then
verifies the same data after PostgreSQL and /data are restored into new
volumes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("GOREVAULT_RECOVERY_URL", "http://127.0.0.1:18081")
EMAIL = "recovery-user@example.invalid"
PASSWORD_HASH = "goreevault-recovery-client-auth-hash-v1"
DEVICE_ID = "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff"
CIPHER_NAME = "2.goreevault-recovery-encrypted-name-v1"
ATTACHMENT_FILENAME = "2.goreevault-recovery-encrypted-filename"
ATTACHMENT_KEY = "2.goreevault-recovery-encrypted-attachment-key"
ATTACHMENT_BYTES = b"goreevault-recovery-encrypted-attachment-payload-v1\x00\x01\xfe\xff"


@dataclass
class Response:
    status: int
    body: bytes
    headers: Any

    def json(self) -> Any:
        if not self.body:
            return None
        return json.loads(self.body.decode("utf-8"))

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_success(resp: Response, label: str) -> None:
    require(200 <= resp.status < 300, f"{label}: HTTP {resp.status}: {resp.text()}")


def request(
    method: str,
    path_or_url: str,
    *,
    json_body: Any | None = None,
    form: dict[str, str] | None = None,
    raw_body: bytes | None = None,
    content_type: str | None = None,
    token: str | None = None,
    absolute: bool = False,
) -> Response:
    body_count = sum(value is not None for value in (json_body, form, raw_body))
    require(body_count <= 1, "request may contain only one body type")

    headers = {"User-Agent": "GoreeVault-Recovery-Harness/0.2"}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif raw_body is not None:
        data = raw_body
        if content_type:
            headers["Content-Type"] = content_type

    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = path_or_url if absolute else BASE_URL + path_or_url
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return Response(resp.status, resp.read(), resp.headers)
    except urllib.error.HTTPError as exc:
        return Response(exc.code, exc.read(), exc.headers)


def multipart_upload(path: str, content: bytes, token: str) -> Response:
    boundary = "----GoreeVaultRecoveryBoundary112233445566"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="data"; filename="{ATTACHMENT_FILENAME}"\r\n'.encode(),
            b"Content-Type: application/octet-stream\r\n\r\n",
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return request(
        "POST",
        path,
        raw_body=body,
        content_type=f"multipart/form-data; boundary={boundary}",
        token=token,
    )


def wait_for_server(timeout: int = 180) -> None:
    deadline = time.monotonic() + timeout
    last = "not started"
    while time.monotonic() < deadline:
        try:
            resp = request("GET", "/alive")
            if resp.status == 200:
                print("PASS  recovery server healthy")
                return
            last = f"HTTP {resp.status}: {resp.text()}"
        except Exception as exc:
            last = repr(exc)
        time.sleep(2)
    raise AssertionError(f"GoreeVault recovery server did not become healthy: {last}")


def kdf() -> dict[str, Any]:
    return {
        "kdf": 0,
        "kdfIterations": 600000,
        "kdfMemory": None,
        "kdfParallelism": None,
    }


def registration_payload() -> dict[str, Any]:
    return {
        "email": EMAIL,
        "name": "GoreeVault Recovery User",
        "masterPasswordAuthentication": {
            "kdf": kdf(),
            "salt": EMAIL,
            "hash": PASSWORD_HASH,
        },
        "masterPasswordUnlock": {
            "kdf": kdf(),
            "salt": EMAIL,
            "key": "2.recovery-encrypted-user-key",
        },
        "keys": {
            "encryptedPrivateKey": "2.recovery-encrypted-private-key",
            "publicKey": "recovery-public-key",
        },
    }


def register() -> None:
    resp = request("POST", "/identity/accounts/register", json_body=registration_payload())
    require_success(resp, "recovery account registration")
    print("PASS  recovery account registered")


def login() -> str:
    resp = request(
        "POST",
        "/identity/connect/token",
        form={
            "grant_type": "password",
            "client_id": "web",
            "scope": "api offline_access",
            "username": EMAIL,
            "password": PASSWORD_HASH,
            "device_identifier": DEVICE_ID,
            "device_name": "GoreeVault Recovery Harness",
            "device_type": "14",
        },
    )
    require_success(resp, "recovery login")
    body = resp.json()
    require(isinstance(body, dict), "recovery login did not return an object")
    token = body.get("access_token")
    require(isinstance(token, str) and token, "recovery login did not return access_token")
    print("PASS  recovery account login")
    return token


def cipher_payload() -> dict[str, Any]:
    return {
        "type": 1,
        "name": CIPHER_NAME,
        "notes": "2.recovery-encrypted-notes",
        "favorite": False,
        "reprompt": 0,
        "login": {
            "username": "2.recovery-encrypted-username",
            "password": "2.recovery-encrypted-password",
            "totp": None,
            "uris": [{"uri": "2.recovery-encrypted-uri", "match": None}],
        },
    }


def object_id(body: Any, label: str) -> str:
    require(isinstance(body, dict), f"{label} did not return an object")
    value = body.get("id") or body.get("Id")
    require(isinstance(value, str) and value, f"{label} response missing id: {body}")
    return value


def sync(token: str) -> dict[str, Any]:
    resp = request("GET", "/api/sync", token=token)
    require_success(resp, "recovery sync")
    body = resp.json()
    require(isinstance(body, dict), "recovery sync did not return an object")
    require(isinstance(body.get("ciphers"), list), "recovery sync missing ciphers")
    return body


def seed(state_path: Path) -> None:
    wait_for_server()
    register()
    token = login()

    resp = request("POST", "/api/ciphers", json_body=cipher_payload(), token=token)
    require_success(resp, "recovery cipher create")
    cipher = resp.json()
    cipher_id = object_id(cipher, "recovery cipher create")
    require(cipher.get("name") == CIPHER_NAME or cipher.get("Name") == CIPHER_NAME, "recovery cipher name changed")
    print("PASS  recovery cipher seeded")

    resp = request(
        "POST",
        f"/api/ciphers/{cipher_id}/attachment/v2",
        json_body={
            "key": ATTACHMENT_KEY,
            "fileName": ATTACHMENT_FILENAME,
            "fileSize": len(ATTACHMENT_BYTES),
        },
        token=token,
    )
    require_success(resp, "recovery attachment metadata create")
    attachment = resp.json()
    require(isinstance(attachment, dict), "recovery attachment create did not return an object")
    attachment_id = attachment.get("attachmentId")
    upload_url = attachment.get("url")
    require(isinstance(attachment_id, str) and attachment_id, "recovery attachment missing attachmentId")
    require(isinstance(upload_url, str) and upload_url.startswith("/ciphers/"), "recovery attachment upload URL invalid")

    resp = multipart_upload("/api" + upload_url, ATTACHMENT_BYTES, token)
    require_success(resp, "recovery attachment upload")
    print("PASS  recovery attachment seeded")

    synced = sync(token)
    require(
        any(
            isinstance(item, dict)
            and (item.get("id") == cipher_id or item.get("Id") == cipher_id)
            and (item.get("name") == CIPHER_NAME or item.get("Name") == CIPHER_NAME)
            for item in synced["ciphers"]
        ),
        "seeded recovery cipher missing from sync",
    )

    state = {
        "cipher_id": cipher_id,
        "attachment_id": attachment_id,
        "attachment_sha256": hashlib.sha256(ATTACHMENT_BYTES).hexdigest(),
        "attachment_size": len(ATTACHMENT_BYTES),
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("PASS  recovery seed state recorded")


def verify(state_path: Path) -> None:
    wait_for_server()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    cipher_id = state["cipher_id"]
    attachment_id = state["attachment_id"]

    token = login()
    synced = sync(token)
    matches = [
        item
        for item in synced["ciphers"]
        if isinstance(item, dict) and (item.get("id") == cipher_id or item.get("Id") == cipher_id)
    ]
    require(len(matches) == 1, "restored sync did not contain exactly one seeded cipher")
    restored_name = matches[0].get("name") or matches[0].get("Name")
    require(restored_name == CIPHER_NAME, "restored cipher ciphertext changed")
    print("PASS  restored account and cipher sync")

    metadata_path = f"/api/ciphers/{cipher_id}/attachment/{attachment_id}"
    resp = request("GET", metadata_path, token=token)
    require_success(resp, "restored attachment metadata")
    metadata = resp.json()
    require(isinstance(metadata, dict), "restored attachment metadata was not an object")
    require(metadata.get("id") == attachment_id, "restored attachment id changed")
    require(metadata.get("fileName") == ATTACHMENT_FILENAME, "restored attachment filename ciphertext changed")
    require(metadata.get("key") == ATTACHMENT_KEY, "restored attachment key ciphertext changed")
    require(metadata.get("size") == str(state["attachment_size"]), "restored attachment size changed")
    download_url = metadata.get("url")
    require(isinstance(download_url, str) and download_url, "restored attachment missing download URL")

    resp = request("GET", download_url, absolute=True)
    require_success(resp, "restored attachment download")
    digest = hashlib.sha256(resp.body).hexdigest()
    require(digest == state["attachment_sha256"], "restored attachment bytes changed")
    require(resp.body == ATTACHMENT_BYTES, "restored attachment payload mismatch")
    print("PASS  restored attachment byte integrity")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("seed", "verify"), required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.mode == "seed":
            seed(args.state)
        else:
            verify(args.state)
    except Exception as exc:
        print(f"FAIL  {exc}", file=os.sys.stderr)
        return 1

    print(f"PASS  GoreeVault recovery mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
