#!/usr/bin/env python3
"""GoreeVault black-box compatibility smoke tests.

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
        if not self.body:
            return None
        return json.loads(self.body.decode("utf-8"))

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
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif content_type is not None:
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
    require(400 <= resp.status < 500, f"{label}: expected authorization/client denial, got HTTP {resp.status}: {resp.text()}")


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


def kdf() -> dict[str, Any]:
    return {
        "kdf": 0,
        "kdfIterations": 600000,
        "kdfMemory": None,
        "kdfParallelism": None,
    }


def registration_payload(email: str, password_hash: str, name: str) -> dict[str, Any]:
    marker = email.split("@", 1)[0]
    return {
        "email": email,
        "name": name,
        "masterPasswordAuthentication": {
            "kdf": kdf(),
            "salt": email,
            "hash": password_hash,
        },
        "masterPasswordUnlock": {
            "kdf": kdf(),
            "salt": email,
            "key": f"2.compat-encrypted-user-key-{marker}",
        },
        "keys": {
            "encryptedPrivateKey": f"2.compat-encrypted-private-key-{marker}",
            "publicKey": f"compat-public-key-{marker}",
        },
    }


def prelogin(email: str = OWNER_EMAIL) -> None:
    resp = request("POST", "/identity/accounts/prelogin", json_body={"email": email})
    require_success(resp, "prelogin")
    body = resp.json()
    require(isinstance(body, dict), "prelogin did not return an object")
    print("PASS  prelogin API contract")


def closed_registration_test() -> None:
    wait_for_server()
    prelogin()
    resp = request(
        "POST",
        "/identity/accounts/register",
        json_body=registration_payload(OWNER_EMAIL, OWNER_PASSWORD_HASH, "GoreeVault Compatibility Owner"),
    )
    require(400 <= resp.status < 500, f"closed registration unexpectedly returned HTTP {resp.status}")
    require(
        "Registration not allowed" in resp.text(),
        f"closed registration returned an unexpected error: {resp.text()}",
    )
    print("PASS  public registration disabled")


def register(email: str, password_hash: str, name: str, label: str) -> None:
    resp = request(
        "POST",
        "/identity/accounts/register",
        json_body=registration_payload(email, password_hash, name),
    )
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
    access = body.get("access_token")
    refresh = body.get("refresh_token")
    require(isinstance(access, str) and access, "login did not return access_token")
    require(isinstance(refresh, str) and refresh, "login did not return refresh_token")
    print(f"PASS  password login ({label})")
    return access, refresh


def refresh_login(refresh_token: str) -> str:
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
    require(isinstance(access, str) and access, "refresh did not return access_token")
    print("PASS  refresh-token rotation")
    return access


def sync(token: str) -> dict[str, Any]:
    resp = request("GET", "/api/sync", token=token)
    require_success(resp, "sync")
    body = resp.json()
    require(isinstance(body, dict), "sync did not return an object")
    require(isinstance(body.get("ciphers"), list), "sync did not return ciphers list")
    require(isinstance(body.get("profile"), dict), "sync did not return profile")
    return body


def cipher_payload(
    name: str,
    *,
    organization_id: str | None = None,
    key: str | None = None,
) -> dict[str, Any]:
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


def get_id(body: dict[str, Any], label: str = "response") -> str:
    value = body.get("id") or body.get("Id")
    require(isinstance(value, str) and value, f"{label} missing id: {body}")
    return value


def contains_id(items: Any, item_id: str) -> bool:
    return isinstance(items, list) and any(
        isinstance(item, dict) and (item.get("id") == item_id or item.get("Id") == item_id) for item in items
    )


def cipher_crud(token: str) -> None:
    initial_name = "2.compat-encrypted-name-v1"
    updated_name = "2.compat-encrypted-name-v2"

    resp = request("POST", "/api/ciphers", json_body=cipher_payload(initial_name), token=token)
    require_success(resp, "create cipher")
    created = resp.json()
    require(isinstance(created, dict), "create cipher did not return an object")
    cipher_id = get_id(created, "cipher response")
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

    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=token)
    require_success(resp, "delete cipher")
    print("PASS  cipher delete")

    synced = sync(token)
    require(not contains_id(synced["ciphers"], cipher_id), "deleted cipher remained in sync response")
    print("PASS  vault sync after delete")


def organization_and_collection_tests(owner_token: str, outsider_token: str) -> tuple[str, str, str]:
    org_payload = {
        "billingEmail": OWNER_EMAIL,
        "collectionName": "2.compat-encrypted-default-collection",
        "key": "2.compat-encrypted-organization-key",
        "name": "GoreeVault Compatibility Organization",
        "planType": 0,
    }
    resp = request("POST", "/api/organizations", json_body=org_payload, token=owner_token)
    require_success(resp, "create organization")
    org_body = resp.json()
    require(isinstance(org_body, dict), "create organization did not return an object")
    org_id = get_id(org_body, "organization response")
    print("PASS  organization create")

    resp = request("GET", f"/api/organizations/{org_id}", token=owner_token)
    require_success(resp, "read organization")
    print("PASS  organization owner access")

    resp = request("GET", f"/api/organizations/{org_id}", token=outsider_token)
    require_denied(resp, "outsider organization read")
    print("PASS  organization outsider denied")

    resp = request("GET", f"/api/organizations/{org_id}/collections", token=owner_token)
    require_success(resp, "list organization collections")
    collection_list = resp.json()
    require(isinstance(collection_list, dict), "collection list did not return an object")
    require(isinstance(collection_list.get("data"), list), "collection list did not return data list")
    require(len(collection_list["data"]) >= 1, "organization did not contain its initial collection")
    print("PASS  initial organization collection")

    new_collection_payload = {
        "name": "2.compat-encrypted-gated-collection",
        "groups": [],
        "users": [],
        "externalId": None,
    }
    resp = request(
        "POST",
        f"/api/organizations/{org_id}/collections",
        json_body=new_collection_payload,
        token=owner_token,
    )
    require_success(resp, "create organization collection")
    collection_body = resp.json()
    require(isinstance(collection_body, dict), "create collection did not return an object")
    collection_id = get_id(collection_body, "collection response")
    print("PASS  organization collection create")

    resp = request(
        "GET",
        f"/api/organizations/{org_id}/collections/{collection_id}/details",
        token=owner_token,
    )
    require_success(resp, "read collection details")
    print("PASS  collection owner access")

    resp = request(
        "GET",
        f"/api/organizations/{org_id}/collections/{collection_id}/details",
        token=outsider_token,
    )
    require_denied(resp, "outsider collection read")
    print("PASS  collection outsider denied")

    shared_payload = {
        "cipher": cipher_payload(
            "2.compat-encrypted-org-item",
            organization_id=org_id,
            key="2.compat-encrypted-org-item-key",
        ),
        "collectionIds": [collection_id],
    }
    resp = request("POST", "/api/ciphers/create", json_body=shared_payload, token=owner_token)
    require_success(resp, "create organization cipher")
    cipher_body = resp.json()
    require(isinstance(cipher_body, dict), "organization cipher did not return an object")
    cipher_id = get_id(cipher_body, "organization cipher response")
    response_org_id = cipher_body.get("organizationId") or cipher_body.get("OrganizationId")
    require(response_org_id == org_id, "organization cipher response did not retain organizationId")
    print("PASS  organization cipher create")

    owner_sync = sync(owner_token)
    require(contains_id(owner_sync["ciphers"], cipher_id), "organization cipher missing from owner sync")
    require(contains_id(owner_sync.get("collections"), collection_id), "created organization collection missing from owner sync")
    print("PASS  organization cipher and collection sync")

    outsider_sync = sync(outsider_token)
    require(not contains_id(outsider_sync["ciphers"], cipher_id), "organization cipher leaked into outsider sync")
    resp = request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token)
    require_denied(resp, "outsider organization cipher read")
    print("PASS  organization cipher outsider denied")

    return org_id, collection_id, cipher_id


def multipart_file(field: str, filename: str, content: bytes) -> tuple[bytes, str]:
    boundary = "----GoreeVaultCompatBoundary7MA4YWxkTrZu0gW"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode(),
            b"Content-Type: application/octet-stream\r\n\r\n",
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return body, f"multipart/form-data; boundary={boundary}"


def attachment_tests(owner_token: str, outsider_token: str, cipher_id: str) -> None:
    attachment_bytes = b"goreevault-compat-attachment-v1\x00opaque-ciphertext"
    metadata_payload = {
        "key": "2.compat-encrypted-attachment-key",
        "fileName": "2.compat-encrypted-attachment-name",
        "fileSize": len(attachment_bytes),
        "adminRequest": False,
    }
    resp = request(
        "POST",
        f"/api/ciphers/{cipher_id}/attachment/v2",
        json_body=metadata_payload,
        token=owner_token,
    )
    require_success(resp, "create attachment metadata")
    upload_data = resp.json()
    require(isinstance(upload_data, dict), "attachment metadata did not return an object")
    attachment_id = upload_data.get("attachmentId")
    upload_url = upload_data.get("url")
    require(isinstance(attachment_id, str) and attachment_id, "attachment metadata missing attachmentId")
    require(isinstance(upload_url, str) and upload_url.startswith("/ciphers/"), "attachment metadata missing upload URL")
    print("PASS  attachment metadata create")

    resp = request(
        "GET",
        f"/api/ciphers/{cipher_id}/attachment/{attachment_id}",
        token=outsider_token,
    )
    require_denied(resp, "outsider attachment metadata read")
    print("PASS  attachment metadata outsider denied")

    multipart_body, content_type = multipart_file("data", "compat.bin", attachment_bytes)
    resp = request(
        "POST",
        "/api" + upload_url,
        raw_body=multipart_body,
        content_type=content_type,
        token=owner_token,
    )
    require_success(resp, "upload attachment data")
    print("PASS  attachment data upload")

    resp = request(
        "GET",
        f"/api/ciphers/{cipher_id}/attachment/{attachment_id}",
        token=owner_token,
    )
    require_success(resp, "read attachment metadata")
    attachment = resp.json()
    require(isinstance(attachment, dict), "attachment read did not return an object")
    require((attachment.get("id") or attachment.get("Id")) == attachment_id, "attachment id mismatch")
    download_url = attachment.get("url") or attachment.get("Url")
    require(isinstance(download_url, str) and download_url.startswith(BASE_URL + "/attachments/"), "invalid attachment download URL")
    print("PASS  attachment metadata read")

    resp = request("GET", download_url)
    require_success(resp, "download attachment")
    require(resp.body == attachment_bytes, "downloaded attachment bytes did not match uploaded bytes")
    print("PASS  signed attachment download")

    resp = request(
        "DELETE",
        f"/api/ciphers/{cipher_id}/attachment/{attachment_id}",
        token=owner_token,
    )
    require_success(resp, "delete attachment")
    print("PASS  attachment delete")

    resp = request(
        "GET",
        f"/api/ciphers/{cipher_id}/attachment/{attachment_id}",
        token=owner_token,
    )
    require_denied(resp, "deleted attachment read")
    print("PASS  deleted attachment unavailable")


def member_collection_access(collection_id: str, *, read_only: bool) -> dict[str, Any]:
    return {
        "id": collection_id,
        "readOnly": read_only,
        "hidePasswords": False,
        "manage": False,
    }


def set_member_access(
    owner_token: str,
    org_id: str,
    member_id: str,
    collection_id: str,
    *,
    read_only: bool,
) -> None:
    resp = request(
        "PUT",
        f"/api/organizations/{org_id}/users/{member_id}",
        json_body={
            "type": 2,
            "collections": [member_collection_access(collection_id, read_only=read_only)],
            "groups": [],
            "permissions": {},
        },
        token=owner_token,
    )
    require_success(resp, "update member collection access")


def membership_acl_tests(
    owner_token: str,
    outsider_token: str,
    org_id: str,
    collection_id: str,
    cipher_id: str,
) -> None:
    invite_payload = {
        "emails": [OUTSIDER_EMAIL],
        "groups": [],
        "type": 2,
        "collections": [member_collection_access(collection_id, read_only=False)],
        "permissions": {},
    }
    resp = request(
        "POST",
        f"/api/organizations/{org_id}/users/invite",
        json_body=invite_payload,
        token=owner_token,
    )
    require_success(resp, "invite existing organization member")
    print("PASS  existing-account organization invitation")

    resp = request(
        "GET",
        f"/api/organizations/{org_id}/users?includeCollections=true&includeGroups=false",
        token=owner_token,
    )
    require_success(resp, "list organization members")
    member_list = resp.json()
    members = member_list.get("data") if isinstance(member_list, dict) else None
    require(isinstance(members, list), "organization member list missing data")
    matches = [m for m in members if isinstance(m, dict) and m.get("email") == OUTSIDER_EMAIL]
    require(len(matches) == 1, "invited outsider missing or duplicated in organization member list")
    outsider_member = matches[0]
    member_id = get_id(outsider_member, "organization member")
    require(outsider_member.get("status") == 1, f"existing no-mail invite should be Accepted before confirm: {outsider_member}")
    require(contains_id(outsider_member.get("collections"), collection_id), "invited member missing assigned collection")
    print("PASS  no-mail invitation enters accepted state")

    resp = request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token)
    require_denied(resp, "accepted-but-unconfirmed member cipher read")
    print("PASS  accepted member blocked before confirmation")

    resp = request(
        "POST",
        f"/api/organizations/{org_id}/users/{member_id}/confirm",
        json_body={"key": "2.compat-encrypted-member-organization-key"},
        token=owner_token,
    )
    require_success(resp, "confirm organization member")
    print("PASS  organization member confirmation")

    outsider_sync = sync(outsider_token)
    require(contains_id(outsider_sync["ciphers"], cipher_id), "confirmed collection member cannot sync organization cipher")
    require(contains_id(outsider_sync.get("collections"), collection_id), "confirmed member cannot sync assigned collection")
    resp = request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token)
    require_success(resp, "confirmed member read organization cipher")
    print("PASS  confirmed member collection read access")

    writable_payload = cipher_payload(
        "2.compat-encrypted-member-write-v1",
        organization_id=org_id,
        key="2.compat-encrypted-org-item-key",
    )
    resp = request("PUT", f"/api/ciphers/{cipher_id}", json_body=writable_payload, token=outsider_token)
    require_success(resp, "writable collection member cipher update")
    print("PASS  writable collection member update")

    set_member_access(owner_token, org_id, member_id, collection_id, read_only=True)
    resp = request(
        "PUT",
        f"/api/ciphers/{cipher_id}",
        json_body=cipher_payload(
            "2.compat-encrypted-readonly-write-attempt",
            organization_id=org_id,
            key="2.compat-encrypted-org-item-key",
        ),
        token=outsider_token,
    )
    require_denied(resp, "read-only collection member cipher update")
    print("PASS  read-only collection ACL blocks update")

    set_member_access(owner_token, org_id, member_id, collection_id, read_only=False)
    resp = request(
        "PUT",
        f"/api/ciphers/{cipher_id}",
        json_body=cipher_payload(
            "2.compat-encrypted-member-write-v2",
            organization_id=org_id,
            key="2.compat-encrypted-org-item-key",
        ),
        token=outsider_token,
    )
    require_success(resp, "restored writable collection member update")
    print("PASS  writable ACL restoration permits update")

    resp = request("DELETE", f"/api/organizations/{org_id}/users/{member_id}", token=owner_token)
    require_success(resp, "remove organization member")
    print("PASS  organization member removal")

    resp = request("GET", f"/api/ciphers/{cipher_id}", token=outsider_token)
    require_denied(resp, "removed member cipher read")
    outsider_sync = sync(outsider_token)
    require(not contains_id(outsider_sync["ciphers"], cipher_id), "removed member still receives organization cipher in sync")
    print("PASS  removed member loses organization access")


def organization_cleanup(owner_token: str, org_id: str, collection_id: str, cipher_id: str) -> None:
    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=owner_token)
    require_success(resp, "delete organization cipher")

    resp = request(
        "DELETE",
        f"/api/organizations/{org_id}/collections/{collection_id}",
        token=owner_token,
    )
    require_success(resp, "delete organization collection")

    resp = request("GET", f"/api/organizations/{org_id}/collections", token=owner_token)
    require_success(resp, "verify collection cleanup")
    body = resp.json()
    data = body.get("data") if isinstance(body, dict) else None
    require(isinstance(data, list), "collection cleanup response did not contain data list")
    require(not contains_id(data, collection_id), "deleted organization collection remained visible")
    print("PASS  organization test cleanup")


def full_test() -> None:
    wait_for_server()
    prelogin()
    register(OWNER_EMAIL, OWNER_PASSWORD_HASH, "GoreeVault Compatibility Owner", "owner")
    owner_access, refresh = login(OWNER_EMAIL, OWNER_PASSWORD_HASH, OWNER_DEVICE_ID, "owner")
    first_sync = sync(owner_access)
    require(first_sync["ciphers"] == [], "new owner account unexpectedly contained ciphers")
    print("PASS  clean-account initial sync")
    owner_access = refresh_login(refresh)
    cipher_crud(owner_access)

    register(OUTSIDER_EMAIL, OUTSIDER_PASSWORD_HASH, "GoreeVault Compatibility Outsider", "outsider")
    outsider_access, _ = login(OUTSIDER_EMAIL, OUTSIDER_PASSWORD_HASH, OUTSIDER_DEVICE_ID, "outsider")

    org_id, collection_id, org_cipher_id = organization_and_collection_tests(owner_access, outsider_access)
    attachment_tests(owner_access, outsider_access, org_cipher_id)
    membership_acl_tests(owner_access, outsider_access, org_id, collection_id, org_cipher_id)
    organization_cleanup(owner_access, org_id, collection_id, org_cipher_id)


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
