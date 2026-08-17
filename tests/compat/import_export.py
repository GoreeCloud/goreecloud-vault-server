#!/usr/bin/env python3
"""Import/export regression fixtures for GoreeVault compatibility."""

from __future__ import annotations

from typing import Any

from compat import (
    DEVICE_ID,
    EMAIL,
    OUTSIDER_DEVICE_ID,
    OUTSIDER_EMAIL,
    OUTSIDER_PASSWORD_HASH,
    PASSWORD_HASH,
    cipher_payload,
    get_id,
    login_account,
    register_account,
    request,
    require,
    require_denied,
    require_success,
    sync,
    wait_for_server,
)


def personal_import_test(owner_token: str) -> None:
    folder_name = "2.compat-encrypted-import-folder"
    cipher_name = "2.compat-encrypted-import-cipher"
    payload = {
        "folders": [{"name": folder_name}],
        "ciphers": [cipher_payload(cipher_name)],
        "folderRelationships": [{"key": 0, "value": 0}],
    }

    resp = request("POST", "/api/ciphers/import", json_body=payload, token=owner_token)
    require_success(resp, "personal vault import")

    synced = sync(owner_token)
    folders = synced.get("folders")
    ciphers = synced.get("ciphers")
    require(isinstance(folders, list), "import sync missing folders list")
    require(isinstance(ciphers, list), "import sync missing ciphers list")

    folder_matches = [item for item in folders if isinstance(item, dict) and item.get("name") == folder_name]
    cipher_matches = [item for item in ciphers if isinstance(item, dict) and item.get("name") == cipher_name]
    require(len(folder_matches) == 1, "imported folder missing or duplicated")
    require(len(cipher_matches) == 1, "imported cipher missing or duplicated")

    folder_id = get_id(folder_matches[0])
    cipher_id = get_id(cipher_matches[0])
    imported_folder_id = cipher_matches[0].get("folderId") or cipher_matches[0].get("FolderId")
    require(imported_folder_id == folder_id, "imported cipher was not linked to imported folder")
    print("PASS  personal import folder/cipher relationship")

    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=owner_token)
    require_success(resp, "delete imported cipher")
    resp = request("DELETE", f"/api/folders/{folder_id}", token=owner_token)
    require_success(resp, "delete imported folder")
    print("PASS  personal import fixture cleanup")


def contains_id(value: Any, expected_id: str) -> bool:
    return isinstance(value, list) and any(
        isinstance(item, dict) and (item.get("id") == expected_id or item.get("Id") == expected_id)
        for item in value
    )


def organization_export_test(owner_token: str, outsider_token: str) -> None:
    resp = request(
        "POST",
        "/api/organizations",
        json_body={
            "billingEmail": EMAIL,
            "collectionName": "2.compat-encrypted-export-collection",
            "key": "2.compat-encrypted-export-organization-key",
            "name": "GoreeVault Export Fixture Organization",
            "keys": {
                "encryptedPrivateKey": "2.compat-encrypted-export-private-key",
                "publicKey": "compat-export-public-key",
            },
            "planType": 0,
        },
        token=owner_token,
    )
    require_success(resp, "create export fixture organization")
    organization = resp.json()
    require(isinstance(organization, dict), "export fixture organization did not return an object")
    org_id = get_id(organization)

    resp = request("GET", f"/api/organizations/{org_id}/collections", token=owner_token)
    require_success(resp, "get export fixture collections")
    body = resp.json()
    collections = body.get("data") if isinstance(body, dict) else None
    require(isinstance(collections, list) and len(collections) == 1, "export fixture initial collection missing")
    collection = collections[0]
    require(isinstance(collection, dict), "export fixture collection was not an object")
    collection_id = get_id(collection)

    organization_cipher = cipher_payload("2.compat-encrypted-export-cipher")
    organization_cipher.update(
        {
            "organizationId": org_id,
            "key": "2.compat-encrypted-export-cipher-key",
        }
    )
    resp = request(
        "POST",
        "/api/ciphers/create",
        json_body={"cipher": organization_cipher, "collectionIds": [collection_id]},
        token=owner_token,
    )
    require_success(resp, "create export fixture cipher")
    cipher = resp.json()
    require(isinstance(cipher, dict), "export fixture cipher did not return an object")
    cipher_id = get_id(cipher)

    resp = request("GET", f"/api/organizations/{org_id}/export", token=owner_token)
    require_success(resp, "organization export")
    exported = resp.json()
    require(isinstance(exported, dict), "organization export did not return an object")
    require(contains_id(exported.get("collections"), collection_id), "organization export missing collection")
    require(contains_id(exported.get("ciphers"), cipher_id), "organization export missing cipher")
    print("PASS  organization export includes collection and cipher")

    resp = request("GET", f"/api/organizations/{org_id}/export", token=outsider_token)
    require_denied(resp, "outsider organization export")
    print("PASS  organization export outsider denied")

    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=owner_token)
    require_success(resp, "delete export fixture cipher")


def main() -> int:
    wait_for_server()
    register_account(EMAIL, PASSWORD_HASH, "GoreeVault Import Export Owner", "compat-import-export")
    register_account(
        OUTSIDER_EMAIL,
        OUTSIDER_PASSWORD_HASH,
        "GoreeVault Import Export Outsider",
        "compat-import-export-outsider",
    )
    owner_token, _owner_refresh = login_account(
        EMAIL,
        PASSWORD_HASH,
        DEVICE_ID,
        "GoreeVault Import Export Owner Harness",
    )
    outsider_token, _outsider_refresh = login_account(
        OUTSIDER_EMAIL,
        OUTSIDER_PASSWORD_HASH,
        OUTSIDER_DEVICE_ID,
        "GoreeVault Import Export Outsider Harness",
    )

    personal_import_test(owner_token)
    organization_export_test(owner_token, outsider_token)
    print("PASS  GoreeVault import/export compatibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
