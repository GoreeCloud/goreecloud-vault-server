#!/usr/bin/env python3
"""GoreeVault black-box compatibility tests.

The harness deliberately treats encrypted vault values as opaque strings. That
matches the server's responsibility: clients perform vault encryption and the
server stores/synchronizes ciphertext without decrypting it.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE_URL = "http://127.0.0.1:18080"
EMAIL = "compat-user@example.invalid"
PASSWORD_HASH = "goreevault-compat-client-auth-hash-v1"
DEVICE_ID = "11111111-2222-4333-8444-555555555555"
ATTACHMENT_BYTES = b"goreevault-compat-encrypted-attachment-payload-v1\x00\x01\xff"


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


def request_url(
    method: str,
    url: str,
    *,
    json_body: Any | None = None,
    form: dict[str, str] | None = None,
    raw_body: bytes | None = None,
    content_type: str | None = None,
    token: str | None = None,
) -> Response:
    body_count = sum(value is not None for value in (json_body, form, raw_body))
    require(body_count <= 1, "request may contain only one body type")

    headers = {"User-Agent": "GoreeVault-Compatibility-Harness/0.2"}
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

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return Response(resp.status, resp.read(), resp.headers)
    except urllib.error.HTTPError as exc:
        return Response(exc.code, exc.read(), exc.headers)


def request(
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    form: dict[str, str] | None = None,
    raw_body: bytes | None = None,
    content_type: str | None = None,
    token: str | None = None,
) -> Response:
    return request_url(
        method,
        BASE_URL + path,
        json_body=json_body,
        form=form,
        raw_body=raw_body,
        content_type=content_type,
        token=token,
    )


def multipart_file_request(path: str, *, filename: str, content: bytes, token: str) -> Response:
    boundary = "----GoreeVaultCompatBoundaryA1B2C3D4E5F6"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="data"; filename="{filename}"\r\n'.encode(),
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_success(resp: Response, label: str) -> None:
    require(200 <= resp.status < 300, f"{label}: HTTP {resp.status}: {resp.text()}")


def wait_for_server(timeout: int = 180) -> None:
    deadline = time.monotonic() + timeout
    last = "not started"
    while time.monotonic() < deadline:
        try:
            resp = request("GET", "/alive")
            if resp.status == 200:
                require(resp.body, "/alive returned an empty body")
                print("PASS  database-backed /alive")
                return
            last = f"HTTP {resp.status}: {resp.text()}"
        except Exception as exc:  # server may still be starting
            last = repr(exc)
        time.sleep(2)
    raise AssertionError(f"GoreeVault did not become healthy: {last}")


def health_contract() -> None:
    resp = request("HEAD", "/alive")
    require_success(resp, "HEAD /alive")
    print("PASS  HEAD /alive")

    resp = request("GET", "/api/alive")
    require_success(resp, "/api/alive")
    require(resp.body, "/api/alive returned an empty body")
    print("PASS  database-backed /api/alive")


def config_contract(*, registration_disabled: bool) -> None:
    resp = request("GET", "/api/config")
    require_success(resp, "config")
    body = resp.json()
    require(isinstance(body, dict), "config did not return an object")
    require(body.get("object") == "config", "config object marker changed")

    server = body.get("server")
    require(isinstance(server, dict), "config did not return server metadata")
    require(server.get("name") == "GoreeVault", f"unexpected server name: {server}")
    require(
        server.get("url") == "https://github.com/GoreeCloud/goreevault-server",
        f"unexpected GoreeVault source URL: {server}",
    )

    settings = body.get("settings")
    require(isinstance(settings, dict), "config did not return settings")
    require(
        settings.get("disableUserRegistration") is registration_disabled,
        "config registration policy does not match runtime policy",
    )

    environment = body.get("environment")
    require(isinstance(environment, dict), "config did not return environment URLs")
    require(str(environment.get("api", "")).endswith("/api"), "config API URL is invalid")
    require(str(environment.get("identity", "")).endswith("/identity"), "config identity URL is invalid")
    print("PASS  GoreeVault config and server identity")


def unauthenticated_sync_denied() -> None:
    resp = request("GET", "/api/sync")
    require(resp.status in (401, 403), f"unauthenticated sync returned HTTP {resp.status}: {resp.text()}")
    print("PASS  unauthenticated vault sync denied")


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
        "name": "GoreeVault Compatibility User",
        "masterPasswordAuthentication": {
            "kdf": kdf(),
            "salt": EMAIL,
            "hash": PASSWORD_HASH,
        },
        "masterPasswordUnlock": {
            "kdf": kdf(),
            "salt": EMAIL,
            "key": "2.compat-encrypted-user-key",
        },
        "keys": {
            "encryptedPrivateKey": "2.compat-encrypted-private-key",
            "publicKey": "compat-public-key",
        },
    }


def prelogin() -> None:
    resp = request("POST", "/identity/accounts/prelogin", json_body={"email": EMAIL})
    require_success(resp, "prelogin")
    body = resp.json()
    require(isinstance(body, dict), "prelogin did not return an object")
    require("kdf" in body, "prelogin response is missing kdf")
    require("kdfIterations" in body, "prelogin response is missing kdfIterations")
    print("PASS  prelogin API contract")


def closed_registration_test() -> None:
    wait_for_server()
    health_contract()
    config_contract(registration_disabled=True)
    unauthenticated_sync_denied()
    prelogin()
    resp = request("POST", "/identity/accounts/register", json_body=registration_payload())
    require(400 <= resp.status < 500, f"closed registration unexpectedly returned HTTP {resp.status}")
    require(
        "Registration not allowed" in resp.text(),
        f"closed registration returned an unexpected error: {resp.text()}",
    )
    print("PASS  public registration disabled")


def register() -> None:
    resp = request("POST", "/identity/accounts/register", json_body=registration_payload())
    require_success(resp, "register")
    print("PASS  isolated test-account registration")


def login() -> tuple[str, str]:
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
            "device_name": "GoreeVault Compatibility Harness",
            "device_type": "14",
        },
    )
    require_success(resp, "login")
    body = resp.json()
    require(isinstance(body, dict), "login did not return an object")
    access = body.get("access_token")
    refresh = body.get("refresh_token")
    require(isinstance(access, str) and access, "login did not return access_token")
    require(isinstance(refresh, str) and refresh, "login did not return refresh_token")
    print("PASS  password login")
    return access, refresh


def refresh_login(refresh_token: str) -> tuple[str, str]:
    resp = request(
        "POST",
        "/identity/connect/token",
        form={
            "grant_type": "refresh_token",
            "client_id": "web",
            "refresh_token": refresh_token,
        },
    )
    require_success(resp, "refresh token")
    body = resp.json()
    access = body.get("access_token") if isinstance(body, dict) else None
    new_refresh = body.get("refresh_token") if isinstance(body, dict) else None
    require(isinstance(access, str) and access, "refresh did not return access_token")
    require(isinstance(new_refresh, str) and new_refresh, "refresh did not return refresh_token")
    require(new_refresh != refresh_token, "refresh token was not rotated")
    print("PASS  refresh-token rotation")
    return access, new_refresh


def refresh_replay_rejected(old_refresh_token: str) -> None:
    resp = request(
        "POST",
        "/identity/connect/token",
        form={
            "grant_type": "refresh_token",
            "client_id": "web",
            "refresh_token": old_refresh_token,
        },
    )
    require(resp.status == 400, f"replayed refresh token returned HTTP {resp.status}: {resp.text()}")
    body = resp.json()
    require(isinstance(body, dict) and body.get("error") == "invalid_grant", "refresh replay was not invalid_grant")
    print("PASS  rotated refresh-token replay rejected")


def sync(token: str) -> dict[str, Any]:
    resp = request("GET", "/api/sync", token=token)
    require_success(resp, "sync")
    body = resp.json()
    require(isinstance(body, dict), "sync did not return an object")
    require(isinstance(body.get("ciphers"), list), "sync did not return ciphers list")
    require(isinstance(body.get("profile"), dict), "sync did not return profile")
    return body


def cipher_payload(name: str) -> dict[str, Any]:
    return {
        "type": 1,
        "name": name,
        "notes": "2.compat-encrypted-notes",
        "favorite": False,
        "reprompt": 0,
        "login": {
            "username": "2.compat-encrypted-username",
            "password": "2.compat-encrypted-password",
            "totp": None,
            "uris": [{"uri": "2.compat-encrypted-uri", "match": None}],
        },
    }


def get_id(body: dict[str, Any]) -> str:
    value = body.get("id") or body.get("Id")
    require(isinstance(value, str) and value, f"cipher response missing id: {body}")
    return value


def attachment_lifecycle(token: str, cipher_id: str) -> None:
    encrypted_filename = "2.compat-encrypted-attachment-filename"
    encrypted_key = "2.compat-encrypted-attachment-key"

    resp = request(
        "POST",
        f"/api/ciphers/{cipher_id}/attachment/v2",
        json_body={
            "key": encrypted_key,
            "fileName": encrypted_filename,
            "fileSize": len(ATTACHMENT_BYTES),
        },
        token=token,
    )
    require_success(resp, "create attachment metadata")
    body = resp.json()
    require(isinstance(body, dict), "attachment create did not return an object")
    attachment_id = body.get("attachmentId")
    upload_url = body.get("url")
    require(isinstance(attachment_id, str) and attachment_id, "attachment create did not return attachmentId")
    require(isinstance(upload_url, str) and upload_url.startswith("/ciphers/"), "attachment upload URL changed")
    print("PASS  attachment metadata create")

    resp = multipart_file_request(
        "/api" + upload_url,
        filename=encrypted_filename,
        content=ATTACHMENT_BYTES,
        token=token,
    )
    require_success(resp, "upload attachment data")
    print("PASS  attachment upload")

    metadata_path = f"/api/ciphers/{cipher_id}/attachment/{attachment_id}"
    resp = request("GET", metadata_path, token=token)
    require_success(resp, "read attachment metadata")
    metadata = resp.json()
    require(isinstance(metadata, dict), "attachment metadata did not return an object")
    require(metadata.get("id") == attachment_id, "attachment metadata id mismatch")
    require(metadata.get("fileName") == encrypted_filename, "attachment encrypted filename changed")
    require(metadata.get("key") == encrypted_key, "attachment encrypted key changed")
    require(metadata.get("size") == str(len(ATTACHMENT_BYTES)), "attachment size mismatch")
    download_url = metadata.get("url")
    require(isinstance(download_url, str) and download_url.startswith(BASE_URL + "/attachments/"), "attachment download URL invalid")
    print("PASS  attachment metadata read")

    resp = request_url("GET", download_url)
    require_success(resp, "download attachment data")
    require(resp.body == ATTACHMENT_BYTES, "attachment download bytes changed")
    print("PASS  attachment download integrity")

    resp = request("DELETE", metadata_path, token=token)
    require_success(resp, "delete attachment")
    print("PASS  attachment delete")

    resp = request("GET", metadata_path, token=token)
    require(400 <= resp.status < 500, f"deleted attachment metadata remained accessible: HTTP {resp.status}")
    resp = request_url("GET", download_url)
    require(400 <= resp.status < 500, f"deleted attachment file remained accessible: HTTP {resp.status}")
    print("PASS  attachment deletion removes metadata and stored file")


def cipher_crud(token: str) -> None:
    initial_name = "2.compat-encrypted-name-v1"
    updated_name = "2.compat-encrypted-name-v2"

    resp = request("POST", "/api/ciphers", json_body=cipher_payload(initial_name), token=token)
    require_success(resp, "create cipher")
    created = resp.json()
    require(isinstance(created, dict), "create cipher did not return an object")
    cipher_id = get_id(created)
    require(created.get("name") == initial_name or created.get("Name") == initial_name, "created cipher name mismatch")
    print("PASS  cipher create")

    resp = request("GET", f"/api/ciphers/{cipher_id}", token=token)
    require_success(resp, "read cipher")
    fetched = resp.json()
    require(isinstance(fetched, dict) and get_id(fetched) == cipher_id, "read cipher id mismatch")
    print("PASS  cipher read")

    resp = request("PUT", f"/api/ciphers/{cipher_id}", json_body=cipher_payload(updated_name), token=token)
    require_success(resp, "update cipher")
    updated = resp.json()
    require(isinstance(updated, dict), "update cipher did not return an object")
    require(updated.get("name") == updated_name or updated.get("Name") == updated_name, "updated cipher name mismatch")
    print("PASS  cipher update")

    synced = sync(token)
    matches = [c for c in synced["ciphers"] if isinstance(c, dict) and (c.get("id") == cipher_id or c.get("Id") == cipher_id)]
    require(len(matches) == 1, "sync did not contain exactly one created cipher")
    synced_name = matches[0].get("name") or matches[0].get("Name")
    require(synced_name == updated_name, "sync did not contain updated cipher")
    print("PASS  vault sync after update")

    attachment_lifecycle(token, cipher_id)

    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=token)
    require_success(resp, "delete cipher")
    print("PASS  cipher delete")

    synced = sync(token)
    require(
        not any(isinstance(c, dict) and (c.get("id") == cipher_id or c.get("Id") == cipher_id) for c in synced["ciphers"]),
        "deleted cipher remained in sync response",
    )
    print("PASS  vault sync after delete")


def full_test() -> None:
    wait_for_server()
    health_contract()
    config_contract(registration_disabled=False)
    unauthenticated_sync_denied()
    prelogin()
    register()
    access, refresh = login()
    first_sync = sync(access)
    require(first_sync["ciphers"] == [], "new account unexpectedly contained ciphers")
    print("PASS  clean-account initial sync")
    access, _new_refresh = refresh_login(refresh)
    refresh_replay_rejected(refresh)
    cipher_crud(access)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("closed", "full"), required=True)
    args = parser.parse_args()

    try:
        if args.mode == "closed":
            closed_registration_test()
        else:
            full_test()
    except Exception as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 1

    print(f"PASS  GoreeVault compatibility mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
