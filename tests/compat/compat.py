#!/usr/bin/env python3
"""Black-box compatibility tests for GoreeVault's Bitwarden-compatible API."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE_URL = "http://127.0.0.1:18080"
OWNER_EMAIL = "compat-owner@example.invalid"
OWNER_PASSWORD_HASH = "goreevault-compat-owner-auth-hash-v1"
OWNER_DEVICE_ID = "11111111-2222-4333-8444-555555555555"
OUTSIDER_EMAIL = "compat-outsider@example.invalid"
OUTSIDER_PASSWORD_HASH = "goreevault-compat-outsider-auth-hash-v1"
OUTSIDER_DEVICE_ID = "66666666-7777-4888-8999-aaaaaaaaaaaa"


@dataclass
class Response:
    status: int
    body: bytes
    headers: Any

    def json(self) -> Any:
        return None if not self.body else json.loads(self.body.decode("utf-8"))

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


def request(
    method: str,
    path_or_url: str,
    *,
    json_body: Any | None = None,
    form: dict[str, str] | None = None,
    raw_body: bytes | None = None,
    content_type: str | None = None,
    token: str | None = None,
) -> Response:
    headers = {"User-Agent": "GoreeVault-Compatibility-Harness/0.2"}
    data = raw_body
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif content_type:
        headers["Content-Type"] = content_type
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = path_or_url if path_or_url.startswith(("http://", "https://")) else BASE_URL + path_or_url
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return Response(resp.status, resp.read(), resp.headers)
    except urllib.error.HTTPError as exc:
        return Response(exc.code, exc.read(), exc.headers)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_success(resp: Response, label: str) -> None:
    require(200 <= resp.status < 300, f"{label}: HTTP {resp.status}: {resp.text()}")


def require_denied(resp: Response, label: str) -> None:
    require(400 <= resp.status < 500, f"{label}: expected 4xx, got HTTP {resp.status}: {resp.text()}")


def get_id(body: dict[str, Any], label: str = "response") -> str:
    value = body.get("id") or body.get("Id")
    require(isinstance(value, str) and value, f"{label} missing id: {body}")
    return value


def contains_id(items: Any, item_id: str) -> bool:
    return isinstance(items, list) and any(
        isinstance(item, dict) and (item.get("id") == item_id or item.get("Id") == item_id) for item in items
    )


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
        except Exception as exc:
            last = repr(exc)
        time.sleep(2)
    raise AssertionError(f"GoreeVault did not become healthy: {last}")


def kdf() -> dict[str, Any]:
    return {"kdf": 0, "kdfIterations": 600000, "kdfMemory": None, "kdfParallelism": None}


def registration_payload(email: str, password_hash: str, name: str) -> dict[str, Any]:
    marker = email.split("@", 1)[0]
    return {
        "email": email,
        "name": name,
        "masterPasswordAuthentication": {"kdf": kdf(), "salt": email, "hash": password_hash},
        "masterPasswordUnlock": {"kdf": kdf(), "salt": email, "key": f"2.compat-user-key-{marker}"},
        "keys": {
            "encryptedPrivateKey": f"2.compat-private-key-{marker}",
            "publicKey": f"compat-public-key-{marker}",
        },
    }


def register(email: str, password_hash: str, name: str, label: str) -> None:
    resp = request("POST", "/identity/accounts/register", json_body=registration_payload(email, password_hash, name))
    require_success(resp, f"register {label}")
    print(f"PASS  isolated {label} registration")


def login(email: str, password_hash: str, device_id: str, label: str) -> tuple[str, str]:
    resp = request(
        "POST",
        "/identity/connect/token",
        form={
            "grant_type": "password",
            "client_id": "web",
            "scope": "api offline_access",
            "username": email,
            "password": password_hash,
            "device_identifier": device_id,
            "device_name": f"GoreeVault Compatibility {label}",
            "device_type": "14",
        },
    )
    require_success(resp, f"login {label}")
    body = resp.json()
    require(isinstance(body, dict), "login did not return an object")
    access, refresh = body.get("access_token"), body.get("refresh_token")
    require(isinstance(access, str) and access, "login missing access_token")
    require(isinstance(refresh, str) and refresh, "login missing refresh_token")
    print(f"PASS  password login ({label})")
    return access, refresh


def sync(token: str) -> dict[str, Any]:
    resp = request("GET", "/api/sync", token=token)
    require_success(resp, "sync")
    body = resp.json()
    require(isinstance(body, dict), "sync did not return an object")
    require(isinstance(body.get("ciphers"), list), "sync missing ciphers")
    require(isinstance(body.get("profile"), dict), "sync missing profile")
    return body


def cipher_payload(name: str, *, organization_id: str | None = None, key: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
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
    if organization_id is not None:
        payload["organizationId"] = organization_id
    if key is not None:
        payload["key"] = key
    return payload


def closed_registration_test() -> None:
    wait_for_server()
    resp = request("POST", "/identity/accounts/prelogin", json_body={"email": OWNER_EMAIL})
    require_success(resp, "prelogin")
    require(isinstance(resp.json(), dict), "prelogin did not return an object")
    print("PASS  prelogin API contract")

    resp = request(
        "POST",
        "/identity/accounts/register",
        json_body=registration_payload(OWNER_EMAIL, OWNER_PASSWORD_HASH, "Compatibility Owner"),
    )
    require_denied(resp, "closed registration")
    require("Registration not allowed" in resp.text(), f"unexpected registration denial: {resp.text()}")
    print("PASS  public registration disabled")


def refresh_login(refresh_token: str) -> str:
    resp = request(
        "POST",
        "/identity/connect/token",
        form={"grant_type": "refresh_token", "client_id": "web", "refresh_token": refresh_token},
    )
    require_success(resp, "refresh token")
    body = resp.json()
    access = body.get("access_token") if isinstance(body, dict) else None
    require(isinstance(access, str) and access, "refresh missing access_token")
    print("PASS  refresh-token rotation")
    return access


def personal_cipher_crud(token: str) -> None:
    v1, v2 = "2.compat-personal-name-v1", "2.compat-personal-name-v2"
    resp = request("POST", "/api/ciphers", json_body=cipher_payload(v1), token=token)
    require_success(resp, "create cipher")
    created = resp.json()
    require(isinstance(created, dict), "create cipher did not return an object")
    cipher_id = get_id(created, "cipher")
    print("PASS  cipher create")

    resp = request("GET", f"/api/ciphers/{cipher_id}", token=token)
    require_success(resp, "read cipher")
    require(get_id(resp.json(), "cipher read") == cipher_id, "cipher read id mismatch")
    print("PASS  cipher read")

    resp = request("PUT", f"/api/ciphers/{cipher_id}", json_body=cipher_payload(v2), token=token)
    require_success(resp, "update cipher")
    updated = resp.json()
    require(isinstance(updated, dict) and (updated.get("name") or updated.get("Name")) == v2, "cipher update mismatch")
    print("PASS  cipher update")

    synced = sync(token)
    matches = [item for item in synced["ciphers"] if isinstance(item, dict) and (item.get("id") == cipher_id or item.get("Id") == cipher_id)]
    require(len(matches) == 1 and (matches[0].get("name") or matches[0].get("Name")) == v2, "updated cipher missing from sync")
    print("PASS  vault sync after update")

    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=token)
    require_success(resp, "delete cipher")
    require(not contains_id(sync(token)["ciphers"], cipher_id), "deleted cipher remained in sync")
    print("PASS  cipher delete and post-delete sync")


def create_org_fixture(owner_token: str, outsider_token: str) -> tuple[str, str, str]:
    resp = request(
        "POST",
        "/api/organizations",
        json_body={
            "billingEmail": OWNER_EMAIL,
            "collectionName": "2.compat-default-collection",
            "key": "2.compat-organization-key",
            "name": "GoreeVault Compatibility Organization",
            "planType": 0,
        },
        token=owner_token,
    )
    require_success(resp, "create organization")
    org = resp.json()
    require(isinstance(org, dict), "organization create did not return an object")
    org_id = get_id(org, "organization")
    print("PASS  organization create")

    require_success(request("GET", f"/api/organizations/{org_id}", token=owner_token), "owner organization read")
    require_denied(request("GET", f"/api/organizations/{org_id}", token=outsider_token), "outsider organization read")
    print("PASS  organization owner access / outsider denial")

    resp = request("GET", f"/api/organizations/{org_id}/collections", token=owner_token)
    require_success(resp, "list initial collections")
    data = resp.json()
    require(isinstance(data, dict) and isinstance(data.get("data"), list) and data["data"], "initial collection missing")
    print("PASS  initial organization collection")

    resp = request(
        "POST",
        f"/api/organizations/{org_id}/collections",
        json_body={"name": "2.compat-gated-collection", "groups": [], "users": [], "externalId": None},
        token=owner_token,
    )
    require_success(resp, "create collection")
    collection = resp.json()
    require(isinstance(collection, dict), "collection create did not return an object")
    collection_id = get_id(collection, "collection")
    require_success(
        request("GET", f"/api/organizations/{org_id}/collections/{collection_id}/details", token=owner_token),
        "owner collection read",
    )
    require_denied(
        request("GET", f"/api/organizations/{org_id}/collections/{collection_id}/details", token=outsider_token),
        "outsider collection read",
    )
    print("PASS  collection create / owner access / outsider denial")

    resp = request(
        "POST",
        "/api/ciphers/create",
        json_body={
            "cipher": cipher_payload("2.compat-org-item", organization_id=org_id, key="2.compat-org-item-key"),
            "collectionIds": [collection_id],
        },
        token=owner_token,
    )
    require_success(resp, "create organization cipher")
    cipher = resp.json()
    require(isinstance(cipher, dict), "organization cipher create did not return an object")
    cipher_id = get_id(cipher, "organization cipher")
    require((cipher.get("organizationId") or cipher.get("OrganizationId")) == org_id, "organizationId mismatch")

    owner_sync = sync(owner_token)
    require(contains_id(owner_sync["ciphers"], cipher_id), "organization cipher missing from owner sync")
    require(contains_id(owner_sync.get("collections"), collection_id), "collection missing from owner sync")
    outsider_sync = sync(outsider_token)
    require(not contains_id(outsider_sync["ciphers"], cipher_id), "organization cipher leaked into outsider sync")
    require_denied(request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token), "outsider cipher read")
    print("PASS  organization cipher sync isolation")
    return org_id, collection_id, cipher_id


def multipart_file(content: bytes) -> tuple[bytes, str]:
    boundary = "----GoreeVaultCompatBoundary7MA4YWxkTrZu0gW"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="data"; filename="compat.bin"\r\n',
            b"Content-Type: application/octet-stream\r\n\r\n",
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return body, f"multipart/form-data; boundary={boundary}"


def attachment_test(owner_token: str, outsider_token: str, cipher_id: str) -> None:
    content = b"goreevault-compat-attachment-v1\x00opaque-ciphertext"
    resp = request(
        "POST",
        f"/api/ciphers/{cipher_id}/attachment/v2",
        json_body={
            "key": "2.compat-attachment-key",
            "fileName": "2.compat-attachment-name",
            "fileSize": len(content),
            "adminRequest": False,
        },
        token=owner_token,
    )
    require_success(resp, "create attachment metadata")
    data = resp.json()
    require(isinstance(data, dict), "attachment metadata did not return an object")
    attachment_id, upload_url = data.get("attachmentId"), data.get("url")
    require(isinstance(attachment_id, str) and attachment_id, "attachmentId missing")
    require(isinstance(upload_url, str) and upload_url.startswith("/ciphers/"), "upload URL missing")
    require_denied(
        request("GET", f"/api/ciphers/{cipher_id}/attachment/{attachment_id}", token=outsider_token),
        "outsider attachment metadata",
    )

    body, content_type = multipart_file(content)
    require_success(
        request("POST", "/api" + upload_url, raw_body=body, content_type=content_type, token=owner_token),
        "attachment upload",
    )
    resp = request("GET", f"/api/ciphers/{cipher_id}/attachment/{attachment_id}", token=owner_token)
    require_success(resp, "attachment metadata read")
    attachment = resp.json()
    require(isinstance(attachment, dict), "attachment read did not return an object")
    download_url = attachment.get("url") or attachment.get("Url")
    require(isinstance(download_url, str) and download_url.startswith(BASE_URL + "/attachments/"), "signed URL invalid")
    downloaded = request("GET", download_url)
    require_success(downloaded, "signed attachment download")
    require(downloaded.body == content, "downloaded attachment bytes differ")
    print("PASS  attachment metadata/upload/signed-download bytes")

    require_success(
        request("DELETE", f"/api/ciphers/{cipher_id}/attachment/{attachment_id}", token=owner_token),
        "attachment delete",
    )
    require_denied(
        request("GET", f"/api/ciphers/{cipher_id}/attachment/{attachment_id}", token=owner_token),
        "deleted attachment read",
    )
    print("PASS  attachment delete and post-delete denial")


def collection_access(collection_id: str, read_only: bool) -> dict[str, Any]:
    return {"id": collection_id, "readOnly": read_only, "hidePasswords": False, "manage": False}


def set_member_access(owner_token: str, org_id: str, member_id: str, collection_id: str, read_only: bool) -> None:
    resp = request(
        "PUT",
        f"/api/organizations/{org_id}/users/{member_id}",
        json_body={"type": 2, "collections": [collection_access(collection_id, read_only)], "groups": [], "permissions": {}},
        token=owner_token,
    )
    require_success(resp, "update member collection access")


def membership_acl_test(owner_token: str, outsider_token: str, org_id: str, collection_id: str, cipher_id: str) -> None:
    resp = request(
        "POST",
        f"/api/organizations/{org_id}/users/invite",
        json_body={
            "emails": [OUTSIDER_EMAIL],
            "groups": [],
            "type": 2,
            "collections": [collection_access(collection_id, False)],
            "permissions": {},
        },
        token=owner_token,
    )
    require_success(resp, "invite existing member")

    resp = request(
        "GET",
        f"/api/organizations/{org_id}/users?includeCollections=true&includeGroups=false",
        token=owner_token,
    )
    require_success(resp, "list organization members")
    body = resp.json()
    members = body.get("data") if isinstance(body, dict) else None
    require(isinstance(members, list), "member list missing data")
    matches = [m for m in members if isinstance(m, dict) and m.get("email") == OUTSIDER_EMAIL]
    require(len(matches) == 1, "invited member missing or duplicated")
    member = matches[0]
    member_id = get_id(member, "organization member")
    require(member.get("status") == 1, f"no-mail existing-user invite should be Accepted: {member}")
    require(not contains_id(member.get("collections"), collection_id), "unconfirmed member unexpectedly exposes collection")

    pre_confirm_sync = sync(outsider_token)
    require(not contains_id(pre_confirm_sync["ciphers"], cipher_id), "unconfirmed member sees organization cipher")
    require(not contains_id(pre_confirm_sync.get("collections"), collection_id), "unconfirmed member sees collection")
    require_denied(request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token), "unconfirmed cipher read")
    print("PASS  accepted member remains isolated before confirmation")

    require_success(
        request(
            "POST",
            f"/api/organizations/{org_id}/users/{member_id}/confirm",
            json_body={"key": "2.compat-member-organization-key"},
            token=owner_token,
        ),
        "confirm organization member",
    )

    post_confirm_sync = sync(outsider_token)
    require(contains_id(post_confirm_sync["ciphers"], cipher_id), "confirmed member cannot sync organization cipher")
    require(contains_id(post_confirm_sync.get("collections"), collection_id), "confirmed member cannot sync collection")
    require_success(request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token), "confirmed member cipher read")

    resp = request(
        "GET",
        f"/api/organizations/{org_id}/users/{member_id}?includeCollections=true&includeGroups=false",
        token=owner_token,
    )
    require_success(resp, "confirmed member details")
    confirmed = resp.json()
    require(isinstance(confirmed, dict) and contains_id(confirmed.get("collections"), collection_id), "confirmed member details missing collection")
    print("PASS  confirmation activates collection and cipher visibility")

    def member_update(name: str) -> Response:
        return request(
            "PUT",
            f"/api/ciphers/{cipher_id}",
            json_body=cipher_payload(name, organization_id=org_id, key="2.compat-org-item-key"),
            token=outsider_token,
        )

    require_success(member_update("2.compat-member-write-v1"), "writable member update")
    set_member_access(owner_token, org_id, member_id, collection_id, True)
    require_denied(member_update("2.compat-readonly-write-attempt"), "read-only member update")
    set_member_access(owner_token, org_id, member_id, collection_id, False)
    require_success(member_update("2.compat-member-write-v2"), "restored writable update")
    print("PASS  writable/read-only/writable collection ACL transition")

    require_success(request("DELETE", f"/api/organizations/{org_id}/users/{member_id}", token=owner_token), "member removal")
    require_denied(request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token), "removed member cipher read")
    require(not contains_id(sync(outsider_token)["ciphers"], cipher_id), "removed member still syncs organization cipher")
    print("PASS  member removal revokes organization access")


def cleanup_org_fixture(owner_token: str, org_id: str, collection_id: str, cipher_id: str) -> None:
    require_success(request("DELETE", f"/api/ciphers/{cipher_id}", token=owner_token), "delete organization cipher")
    require_success(
        request("DELETE", f"/api/organizations/{org_id}/collections/{collection_id}", token=owner_token),
        "delete organization collection",
    )
    resp = request("GET", f"/api/organizations/{org_id}/collections", token=owner_token)
    require_success(resp, "verify collection cleanup")
    body = resp.json()
    require(isinstance(body, dict) and not contains_id(body.get("data"), collection_id), "deleted collection remained visible")
    print("PASS  organization fixture cleanup")


def full_test() -> None:
    wait_for_server()
    register(OWNER_EMAIL, OWNER_PASSWORD_HASH, "GoreeVault Compatibility Owner", "owner")
    owner_token, refresh = login(OWNER_EMAIL, OWNER_PASSWORD_HASH, OWNER_DEVICE_ID, "owner")
    require(sync(owner_token)["ciphers"] == [], "new owner account unexpectedly contained ciphers")
    print("PASS  clean-account initial sync")
    owner_token = refresh_login(refresh)
    personal_cipher_crud(owner_token)

    register(OUTSIDER_EMAIL, OUTSIDER_PASSWORD_HASH, "GoreeVault Compatibility Outsider", "outsider")
    outsider_token, _ = login(OUTSIDER_EMAIL, OUTSIDER_PASSWORD_HASH, OUTSIDER_DEVICE_ID, "outsider")

    org_id, collection_id, cipher_id = create_org_fixture(owner_token, outsider_token)
    attachment_test(owner_token, outsider_token, cipher_id)
    membership_acl_test(owner_token, outsider_token, org_id, collection_id, cipher_id)
    cleanup_org_fixture(owner_token, org_id, collection_id, cipher_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("closed", "full"), required=True)
    args = parser.parse_args()
    try:
        closed_registration_test() if args.mode == "closed" else full_test()
    except Exception as exc:
        print(f"FAIL  {exc}")
        return 1
    print(f"PASS  GoreeVault compatibility mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
