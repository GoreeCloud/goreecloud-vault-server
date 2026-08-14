#!/usr/bin/env python3
"""GoreeVault organization membership and collection-scope compatibility tests."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE_URL = "http://127.0.0.1:18080"
OWNER_EMAIL = "org-owner@example.invalid"
OWNER_PASSWORD = "goreevault-org-owner-auth-hash-v1"
OWNER_DEVICE = "10101010-2020-4030-8040-505050505050"
MEMBER_EMAIL = "org-member@example.invalid"
MEMBER_PASSWORD = "goreevault-org-member-auth-hash-v1"
MEMBER_DEVICE = "60606060-7070-4080-8090-a0a0a0a0a0a0"


@dataclass
class Response:
    status: int
    body: bytes

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


def require_denied(resp: Response, label: str) -> None:
    require(resp.status in (401, 403, 404), f"{label}: expected denial, got HTTP {resp.status}: {resp.text()}")


def request(
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    form: dict[str, str] | None = None,
    token: str | None = None,
) -> Response:
    headers = {"User-Agent": "GoreeVault-Org-Membership-Harness/0.2"}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return Response(resp.status, resp.read())
    except urllib.error.HTTPError as exc:
        return Response(exc.code, exc.read())


def wait_for_server(timeout: int = 180) -> None:
    deadline = time.monotonic() + timeout
    last = "not started"
    while time.monotonic() < deadline:
        try:
            resp = request("GET", "/alive")
            if resp.status == 200:
                print("PASS  organization-membership server healthy")
                return
            last = f"HTTP {resp.status}: {resp.text()}"
        except Exception as exc:
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


def register(email: str, password_hash: str, name: str, prefix: str) -> None:
    payload = {
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
            "key": f"2.{prefix}-encrypted-user-key",
        },
        "keys": {
            "encryptedPrivateKey": f"2.{prefix}-encrypted-private-key",
            "publicKey": f"{prefix}-public-key",
        },
    }
    resp = request("POST", "/identity/accounts/register", json_body=payload)
    require_success(resp, f"register {email}")


def login(email: str, password_hash: str, device_id: str, device_name: str) -> str:
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
            "device_name": device_name,
            "device_type": "14",
        },
    )
    require_success(resp, f"login {email}")
    body = resp.json()
    require(isinstance(body, dict), "login did not return an object")
    token = body.get("access_token")
    require(isinstance(token, str) and token, "login did not return access_token")
    return token


def object_id(body: Any, label: str) -> str:
    require(isinstance(body, dict), f"{label} did not return an object")
    value = body.get("id") or body.get("Id")
    require(isinstance(value, str) and value, f"{label} response missing id: {body}")
    return value


def list_ids(resp: Response, label: str) -> set[str]:
    require_success(resp, label)
    body = resp.json()
    require(isinstance(body, dict), f"{label} did not return an object")
    data = body.get("data")
    require(isinstance(data, list), f"{label} did not return data list")
    return {
        value
        for item in data
        if isinstance(item, dict)
        for value in (item.get("id") or item.get("Id"),)
        if isinstance(value, str) and value
    }


def collection_access(collection_id: str, *, read_only: bool = True) -> dict[str, Any]:
    return {
        "id": collection_id,
        "readOnly": read_only,
        "hidePasswords": False,
        "manage": False,
    }


def find_member(owner_token: str, org_id: str) -> dict[str, Any]:
    resp = request(
        "GET",
        f"/api/organizations/{org_id}/users?includeCollections=true",
        token=owner_token,
    )
    require_success(resp, "list organization members")
    body = resp.json()
    require(isinstance(body, dict) and isinstance(body.get("data"), list), "member list response invalid")
    matches = [item for item in body["data"] if isinstance(item, dict) and item.get("email") == MEMBER_EMAIL]
    require(len(matches) == 1, f"expected one organization membership for {MEMBER_EMAIL}: {matches}")
    return matches[0]


def assigned_collection_ids(member: dict[str, Any]) -> set[str]:
    collections = member.get("collections")
    require(isinstance(collections, list), f"membership collections missing: {member}")
    return {
        item.get("id")
        for item in collections
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def main() -> int:
    try:
        wait_for_server()

        register(OWNER_EMAIL, OWNER_PASSWORD, "GoreeVault Org Owner", "org-owner")
        register(MEMBER_EMAIL, MEMBER_PASSWORD, "GoreeVault Restricted Member", "org-member")
        owner_token = login(OWNER_EMAIL, OWNER_PASSWORD, OWNER_DEVICE, "GoreeVault Org Owner Harness")
        member_token = login(MEMBER_EMAIL, MEMBER_PASSWORD, MEMBER_DEVICE, "GoreeVault Org Member Harness")
        print("PASS  owner and restricted-member accounts ready")

        resp = request(
            "POST",
            "/api/organizations",
            json_body={
                "billingEmail": OWNER_EMAIL,
                "collectionName": "2.org-default-encrypted-collection",
                "key": "2.org-owner-encrypted-key",
                "name": "GoreeVault Membership Test Organization",
                "keys": {
                    "encryptedPrivateKey": "2.org-encrypted-private-key",
                    "publicKey": "org-public-key",
                },
                "planType": 0,
            },
            token=owner_token,
        )
        require_success(resp, "create membership test organization")
        org_id = object_id(resp.json(), "create membership test organization")

        org_collections_path = f"/api/organizations/{org_id}/collections"
        default_ids = list_ids(request("GET", org_collections_path, token=owner_token), "list default collection")
        require(len(default_ids) == 1, f"expected exactly one default collection, got {default_ids}")
        default_id = next(iter(default_ids))

        resp = request(
            "POST",
            org_collections_path,
            json_body={
                "name": "2.org-assigned-encrypted-collection",
                "groups": [],
                "users": [],
                "externalId": None,
            },
            token=owner_token,
        )
        require_success(resp, "create assigned collection")
        assigned_id = object_id(resp.json(), "create assigned collection")
        require(assigned_id != default_id, "assigned and default collections unexpectedly share an id")
        print("PASS  organization owner created isolated collections")

        resp = request(
            "POST",
            f"/api/organizations/{org_id}/users/invite",
            json_body={
                "emails": [MEMBER_EMAIL],
                "groups": [],
                "type": 2,
                "collections": [collection_access(assigned_id)],
                "permissions": {},
            },
            token=owner_token,
        )
        require_success(resp, "invite existing restricted member")

        member = find_member(owner_token, org_id)
        member_id = object_id(member, "accepted membership")
        require(member.get("status") == 1, f"existing member should auto-accept with mail disabled: {member}")
        require(member.get("type") == 2, f"restricted member type changed: {member}")
        # Accepted memberships are intentionally not effective collection
        # memberships yet. Collection queries require Confirmed status.
        require(assigned_collection_ids(member) == set(), f"accepted member unexpectedly had effective collections: {member}")
        accepted_ids = list_ids(request("GET", "/api/collections", token=member_token), "accepted member collection list")
        require(default_id not in accepted_ids and assigned_id not in accepted_ids, "accepted member received collection access before confirmation")
        print("PASS  accepted member has no effective collection access")

        resp = request(
            "POST",
            f"/api/organizations/{org_id}/users/{member_id}/confirm",
            json_body={"key": "2.org-member-encrypted-key"},
            token=owner_token,
        )
        require_success(resp, "confirm restricted member")
        member = find_member(owner_token, org_id)
        require(member.get("status") == 2, f"member did not become confirmed: {member}")
        require(assigned_collection_ids(member) == {assigned_id}, f"confirmed member assignment mismatch: {member}")
        print("PASS  restricted member confirmed with assigned collection")

        member_ids = list_ids(request("GET", "/api/collections", token=member_token), "member collection list")
        require(assigned_id in member_ids, "confirmed member cannot see assigned collection")
        require(default_id not in member_ids, "confirmed member can see unassigned default collection")
        print("PASS  confirmed member sees only assigned collection")

        require_denied(
            request("GET", org_collections_path, token=member_token),
            "restricted member enumerate all organization collections",
        )
        require_denied(
            request(
                "POST",
                org_collections_path,
                json_body={"name": "forbidden", "groups": [], "users": [], "externalId": None},
                token=member_token,
            ),
            "restricted member create organization collection",
        )
        print("PASS  restricted member cannot manage organization collections")

        resp = request(
            "PUT",
            f"/api/organizations/{org_id}/users/{member_id}",
            json_body={
                "type": 2,
                "collections": [collection_access(default_id)],
                "groups": [],
                "permissions": {},
            },
            token=owner_token,
        )
        require_success(resp, "move restricted member collection assignment")

        member = find_member(owner_token, org_id)
        require(assigned_collection_ids(member) == {default_id}, f"member reassignment did not replace prior access: {member}")
        member_ids = list_ids(request("GET", "/api/collections", token=member_token), "member collection list after move")
        require(default_id in member_ids, "member cannot see newly assigned default collection")
        require(assigned_id not in member_ids, "member retained stale access to removed collection")
        print("PASS  collection reassignment revokes stale access")

        resp = request("DELETE", f"/api/organizations/{org_id}/users/{member_id}", token=owner_token)
        require_success(resp, "remove restricted member")
        member_ids = list_ids(request("GET", "/api/collections", token=member_token), "member collection list after removal")
        require(default_id not in member_ids and assigned_id not in member_ids, "removed member retained organization collection access")
        print("PASS  membership removal revokes collection access")

    except Exception as exc:
        print(f"FAIL  {exc}", file=__import__("sys").stderr)
        return 1

    print("PASS  GoreeVault restricted organization membership lifecycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
