#!/usr/bin/env python3
"""Import/export regression fixtures for the GoreeVault compatibility stack."""

from __future__ import annotations

from typing import Any

from compat import (
    OUTSIDER_DEVICE_ID,
    OUTSIDER_EMAIL,
    OUTSIDER_PASSWORD_HASH,
    OWNER_DEVICE_ID,
    OWNER_EMAIL,
    OWNER_PASSWORD_HASH,
    cipher_payload,
    contains_id,
    get_id,
    login,
    request,
    require,
    require_denied,
    require_success,
    sync,
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

    folder_matches = [f for f in folders if isinstance(f, dict) and f.get("name") == folder_name]
    cipher_matches = [c for c in ciphers if isinstance(c, dict) and c.get("name") == cipher_name]
    require(len(folder_matches) == 1, "imported folder missing or duplicated")
    require(len(cipher_matches) == 1, "imported cipher missing or duplicated")

    folder_id = get_id(folder_matches[0], "imported folder")
    cipher_id = get_id(cipher_matches[0], "imported cipher")
    imported_folder_id = cipher_matches[0].get("folderId") or cipher_matches[0].get("FolderId")
    require(imported_folder_id == folder_id, "imported cipher was not linked to imported folder")
    print("PASS  personal import folder/cipher relationship")

    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=owner_token)
    require_success(resp, "delete imported cipher")
    resp = request("DELETE", f"/api/folders/{folder_id}", token=owner_token)
    require_success(resp, "delete imported folder")
    print("PASS  personal import fixture cleanup")


def organization_export_test(owner_token: str, outsider_token: str) -> None:
    resp = request(
        "POST",
        "/api/organizations",
        json_body={
            "billingEmail": OWNER_EMAIL,
            "collectionName": "2.compat-encrypted-export-collection",
            "key": "2.compat-encrypted-export-organization-key",
            "name": "GoreeVault Export Fixture Organization",
            "planType": 0,
        },
        token=owner_token,
    )
    require_success(resp, "create export fixture organization")
    org = resp.json()
    require(isinstance(org, dict), "export fixture organization did not return an object")
    org_id = get_id(org, "export fixture organization")

    resp = request("GET", f"/api/organizations/{org_id}/collections", token=owner_token)
    require_success(resp, "get export fixture collections")
    body = resp.json()
    collections = body.get("data") if isinstance(body, dict) else None
    require(isinstance(collections, list) and len(collections) == 1, "export fixture initial collection missing")
    collection_id = get_id(collections[0], "export fixture collection")

    resp = request(
        "POST",
        "/api/ciphers/create",
        json_body={
            "cipher": cipher_payload(
                "2.compat-encrypted-export-cipher",
                organization_id=org_id,
                key="2.compat-encrypted-export-cipher-key",
            ),
            "collectionIds": [collection_id],
        },
        token=owner_token,
    )
    require_success(resp, "create export fixture cipher")
    cipher = resp.json()
    require(isinstance(cipher, dict), "export fixture cipher did not return an object")
    cipher_id = get_id(cipher, "export fixture cipher")

    resp = request("GET", f"/api/organizations/{org_id}/export", token=owner_token)
    require_success(resp, "organization export")
    export: Any = resp.json()
    require(isinstance(export, dict), "organization export did not return an object")
    require(contains_id(export.get("collections"), collection_id), "organization export missing collection")
    require(contains_id(export.get("ciphers"), cipher_id), "organization export missing cipher")
    print("PASS  organization export includes collection and cipher")

    resp = request("GET", f"/api/organizations/{org_id}/export", token=outsider_token)
    require_denied(resp, "outsider organization export")
    print("PASS  organization export outsider denied")

    resp = request("DELETE", f"/api/ciphers/{cipher_id}", token=owner_token)
    require_success(resp, "delete export fixture cipher")


def main() -> int:
    owner_token, _ = login(OWNER_EMAIL, OWNER_PASSWORD_HASH, OWNER_DEVICE_ID, "owner-import-export")
    outsider_token, _ = login(
        OUTSIDER_EMAIL,
        OUTSIDER_PASSWORD_HASH,
        OUTSIDER_DEVICE_ID,
        "outsider-import-export",
    )
    personal_import_test(owner_token)
    organization_export_test(owner_token, outsider_token)
    print("PASS  GoreeVault import/export fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
