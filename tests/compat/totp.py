#!/usr/bin/env python3
"""GoreeVault TOTP enrollment, login, replay, and recovery compatibility tests."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE_URL = "http://127.0.0.1:18080"
EMAIL = "totp-user@example.invalid"
PASSWORD_HASH = "goreevault-totp-client-auth-hash-v1"
DEVICE_ID = "12121212-3434-4567-89ab-cdefabcdef12"


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


def request(
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    form: dict[str, str] | None = None,
    token: str | None = None,
) -> Response:
    headers = {"User-Agent": "GoreeVault-TOTP-Harness/0.2"}
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
                print("PASS  TOTP server healthy")
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
        "name": "GoreeVault TOTP User",
        "masterPasswordAuthentication": {
            "kdf": kdf(),
            "salt": EMAIL,
            "hash": PASSWORD_HASH,
        },
        "masterPasswordUnlock": {
            "kdf": kdf(),
            "salt": EMAIL,
            "key": "2.totp-encrypted-user-key",
        },
        "keys": {
            "encryptedPrivateKey": "2.totp-encrypted-private-key",
            "publicKey": "totp-public-key",
        },
    }
    resp = request("POST", "/identity/accounts/register", json_body=payload)
    require_success(resp, "register TOTP account")
    print("PASS  TOTP account registered")


def login(*, provider: int | None = None, two_factor_token: str | None = None) -> Response:
    form = {
        "grant_type": "password",
        "client_id": "web",
        "scope": "api offline_access",
        "username": EMAIL,
        "password": PASSWORD_HASH,
        "device_identifier": DEVICE_ID,
        "device_name": "GoreeVault TOTP Harness",
        "device_type": "14",
    }
    if provider is not None:
        form["two_factor_provider"] = str(provider)
    if two_factor_token is not None:
        form["two_factor_token"] = two_factor_token
    return request("POST", "/identity/connect/token", form=form)


def access_token(resp: Response, label: str) -> str:
    require_success(resp, label)
    body = resp.json()
    require(isinstance(body, dict), f"{label} did not return an object")
    value = body.get("access_token")
    require(isinstance(value, str) and value, f"{label} did not return access_token")
    return value


def decode_base32(secret: str) -> bytes:
    normalized = secret.strip().upper()
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    return base64.b32decode(normalized + padding, casefold=True)


def totp(secret: str, timestamp: int | None = None) -> str:
    if timestamp is None:
        timestamp = int(time.time())
    counter = timestamp // 30
    digest = hmac.new(decode_base32(secret), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{binary % 1_000_000:06d}"


def wait_for_next_step(timeout: int = 35) -> None:
    initial_step = int(time.time()) // 30
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if int(time.time()) // 30 > initial_step:
            time.sleep(0.25)
            return
        time.sleep(0.2)
    raise AssertionError("TOTP time step did not advance")


def require_twofactor_challenge(resp: Response) -> None:
    require(400 <= resp.status < 500, f"login without 2FA unexpectedly returned HTTP {resp.status}")
    body = resp.json()
    require(isinstance(body, dict), f"2FA challenge did not return an object: {resp.text()}")
    require(body.get("error") == "invalid_grant", f"2FA challenge did not return invalid_grant: {body}")
    providers = body.get("TwoFactorProviders")
    require(isinstance(providers, list) and "0" in providers, f"authenticator provider missing from challenge: {body}")
    print("PASS  password login requires authenticator 2FA")


def main() -> int:
    try:
        wait_for_server()
        register()
        initial_access = access_token(login(), "initial password login")
        print("PASS  initial password login before 2FA")

        resp = request(
            "POST",
            "/api/two-factor/get-authenticator",
            json_body={"masterPasswordHash": PASSWORD_HASH},
            token=initial_access,
        )
        require_success(resp, "get authenticator secret")
        body = resp.json()
        require(isinstance(body, dict), "authenticator secret response was not an object")
        require(body.get("enabled") is False, f"authenticator unexpectedly enabled before enrollment: {body}")
        secret = body.get("key")
        require(isinstance(secret, str) and secret, "authenticator secret missing")
        require(len(decode_base32(secret)) == 20, "authenticator secret was not 20 decoded bytes")
        print("PASS  authenticator secret generated")

        enrollment_code = totp(secret)
        resp = request(
            "POST",
            "/api/two-factor/authenticator",
            json_body={
                "key": secret,
                "token": enrollment_code,
                "masterPasswordHash": PASSWORD_HASH,
                "otp": None,
            },
            token=initial_access,
        )
        require_success(resp, "enable authenticator")
        enabled = resp.json()
        require(isinstance(enabled, dict) and enabled.get("enabled") is True, "authenticator did not enable")
        print("PASS  authenticator TOTP enabled")

        require_twofactor_challenge(login())

        replay = login(provider=0, two_factor_token=enrollment_code)
        require(400 <= replay.status < 500, f"enrollment TOTP replay unexpectedly returned HTTP {replay.status}")
        print("PASS  enrollment TOTP replay rejected")

        resp = request(
            "POST",
            "/api/two-factor/get-recover",
            json_body={"masterPasswordHash": PASSWORD_HASH},
            token=initial_access,
        )
        require_success(resp, "get recovery code")
        recovery_body = resp.json()
        require(isinstance(recovery_body, dict), "recovery response was not an object")
        recovery_code = recovery_body.get("code")
        require(isinstance(recovery_code, str) and recovery_code, "recovery code missing")
        print("PASS  2FA recovery code issued")

        wait_for_next_step()
        next_code = totp(secret)
        totp_access = access_token(
            login(provider=0, two_factor_token=next_code),
            "login with next-step TOTP",
        )
        require(totp_access != initial_access, "2FA login did not return a fresh access token")
        print("PASS  next-step authenticator login")

        replay = login(provider=0, two_factor_token=next_code)
        require(400 <= replay.status < 500, f"used TOTP replay unexpectedly returned HTTP {replay.status}")
        print("PASS  used TOTP replay rejected")

        recovery_access = access_token(
            login(provider=8, two_factor_token=recovery_code),
            "login with recovery code",
        )
        print("PASS  recovery-code login")

        resp = request("GET", "/api/two-factor", token=recovery_access)
        require_success(resp, "list 2FA after recovery")
        providers_body = resp.json()
        require(isinstance(providers_body, dict), "2FA list after recovery was not an object")
        require(providers_body.get("data") == [], f"2FA providers remained after recovery: {providers_body}")
        print("PASS  recovery removed authenticator provider")

        access_token(login(), "password login after recovery")
        print("PASS  normal password login restored after recovery")

    except Exception as exc:
        print(f"FAIL  {exc}", file=sys.stderr)
        return 1

    print("PASS  GoreeVault TOTP lifecycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
