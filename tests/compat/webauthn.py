#!/usr/bin/env python3
"""GoreeVault WebAuthn registration-challenge compatibility tests.

This intentionally does not fake a successful hardware authenticator. It proves
that challenge generation is correctly bound to the configured RP, protected
by the master password, rejects malformed attestation data, and does not create
a credential after a failed registration attempt.
"""

from __future__ import annotations

import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE_URL = "http://127.0.0.1:18080"
EXPECTED_ORIGIN = "http://localhost:18080"
EMAIL = "webauthn-user@example.invalid"
PASSWORD_HASH = "goreevault-webauthn-client-auth-hash-v1"
DEVICE_ID = "abababab-cdcd-4e4e-8f8f-101010101010"


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


def require_client_error(resp: Response, label: str) -> None:
    require(400 <= resp.status < 500, f"{label}: expected 4xx, got HTTP {resp.status}: {resp.text()}")


def request(
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    form: dict[str, str] | None = None,
    token: str | None = None,
) -> Response:
    headers = {"User-Agent": "GoreeVault-WebAuthn-Harness/0.2"}
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
                print("PASS  WebAuthn server healthy")
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


def register() -> None:
    payload = {
        "email": EMAIL,
        "name": "GoreeVault WebAuthn User",
        "masterPasswordAuthentication": {
            "kdf": kdf(),
            "salt": EMAIL,
            "hash": PASSWORD_HASH,
        },
        "masterPasswordUnlock": {
            "kdf": kdf(),
            "salt": EMAIL,
            "key": "2.webauthn-encrypted-user-key",
        },
        "keys": {
            "encryptedPrivateKey": "2.webauthn-encrypted-private-key",
            "publicKey": "webauthn-public-key",
        },
    }
    resp = request("POST", "/identity/accounts/register", json_body=payload)
    require_success(resp, "register WebAuthn account")
    print("PASS  WebAuthn account registered")


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
            "device_name": "GoreeVault WebAuthn Harness",
            "device_type": "14",
        },
    )
    require_success(resp, "WebAuthn account login")
    body = resp.json()
    require(isinstance(body, dict), "login did not return an object")
    token = body.get("access_token")
    require(isinstance(token, str) and token, "login did not return access_token")
    return token


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def get_status(token: str) -> dict[str, Any]:
    resp = request(
        "POST",
        "/api/two-factor/get-webauthn",
        json_body={"masterPasswordHash": PASSWORD_HASH},
        token=token,
    )
    require_success(resp, "get WebAuthn status")
    body = resp.json()
    require(isinstance(body, dict), "WebAuthn status was not an object")
    return body


def get_challenge(token: str) -> dict[str, Any]:
    resp = request(
        "POST",
        "/api/two-factor/get-webauthn-challenge",
        json_body={"masterPasswordHash": PASSWORD_HASH},
        token=token,
    )
    require_success(resp, "get WebAuthn registration challenge")
    body = resp.json()
    require(isinstance(body, dict), "WebAuthn challenge was not an object")
    return body


def malformed_registration(challenge: str) -> dict[str, Any]:
    client_data = json.dumps(
        {
            "type": "webauthn.create",
            "challenge": challenge,
            "origin": EXPECTED_ORIGIN,
            "crossOrigin": False,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "id": 1,
        "name": "Invalid CI authenticator",
        "deviceResponse": {
            "id": "AA",
            "rawId": "AA",
            "response": {
                "attestationObject": "AA",
                "clientDataJson": b64url(client_data),
            },
            "type": "public-key",
        },
        "masterPasswordHash": PASSWORD_HASH,
        "otp": None,
    }


def main() -> int:
    try:
        wait_for_server()
        register()
        token = login()
        print("PASS  WebAuthn account login")

        status = get_status(token)
        require(status.get("enabled") is False, f"WebAuthn unexpectedly enabled: {status}")
        require(status.get("keys") == [], f"unexpected WebAuthn registrations: {status}")
        print("PASS  WebAuthn starts disabled with no credentials")

        denied = request(
            "POST",
            "/api/two-factor/get-webauthn-challenge",
            json_body={"masterPasswordHash": "wrong-master-password-hash"},
            token=token,
        )
        require_client_error(denied, "WebAuthn challenge with wrong password")
        print("PASS  WebAuthn challenge is master-password protected")

        challenge_body = get_challenge(token)
        challenge = challenge_body.get("challenge")
        require(isinstance(challenge, str) and challenge, f"challenge missing: {challenge_body}")
        require(challenge_body.get("status") == "ok", f"challenge status invalid: {challenge_body}")
        require(challenge_body.get("errorMessage") == "", f"challenge errorMessage invalid: {challenge_body}")

        rp = challenge_body.get("rp")
        require(isinstance(rp, dict), f"RP metadata missing: {challenge_body}")
        require(rp.get("id") == "localhost", f"unexpected WebAuthn RP id: {rp}")

        user = challenge_body.get("user")
        require(isinstance(user, dict), f"WebAuthn user metadata missing: {challenge_body}")
        require(user.get("name") == EMAIL, f"unexpected WebAuthn user name: {user}")

        selection = challenge_body.get("authenticatorSelection")
        require(isinstance(selection, dict), f"authenticatorSelection missing: {challenge_body}")
        require(selection.get("userVerification") == "discouraged", f"unexpected user verification policy: {selection}")
        print("PASS  WebAuthn challenge uses expected RP and 2FA policy")

        invalid = request(
            "POST",
            "/api/two-factor/webauthn",
            json_body=malformed_registration(challenge),
            token=token,
        )
        require_client_error(invalid, "malformed WebAuthn attestation")
        print("PASS  malformed WebAuthn attestation rejected")

        status = get_status(token)
        require(status.get("enabled") is False, f"failed registration enabled WebAuthn: {status}")
        require(status.get("keys") == [], f"failed registration created a credential: {status}")

        providers = request("GET", "/api/two-factor", token=token)
        require_success(providers, "list 2FA providers after failed WebAuthn registration")
        providers_body = providers.json()
        require(isinstance(providers_body, dict), "2FA provider response was not an object")
        require(providers_body.get("data") == [], f"failed WebAuthn registration created provider state: {providers_body}")
        print("PASS  failed WebAuthn registration leaves no credential/provider")

        second = get_challenge(token)
        second_challenge = second.get("challenge")
        require(isinstance(second_challenge, str) and second_challenge, "second challenge missing")
        require(second_challenge != challenge, "WebAuthn challenge was unexpectedly reused")
        print("PASS  fresh WebAuthn registration challenge generated")

    except Exception as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 1

    print("PASS  GoreeVault WebAuthn challenge and rejection lifecycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
