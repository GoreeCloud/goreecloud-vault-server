#!/usr/bin/env python3
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util

SCRIPT = Path(__file__).with_name("serve_argon2id_browser_harness.py")
spec = importlib.util.spec_from_file_location("harness_server", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def expect_raises(exc_type, func, *args):
    try:
        func(*args)
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def main() -> int:
    assert module.require_loopback("127.0.0.1") == "127.0.0.1"
    assert module.require_loopback("::1") == "::1"
    expect_raises(ValueError, module.require_loopback, "0.0.0.0")
    expect_raises(ValueError, module.require_loopback, "192.168.1.10")
    expect_raises(ValueError, module.require_loopback, "localhost")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name in module.ALLOWED_FILES:
            (root / name).write_bytes(b"test")
        assert module.safe_candidate_path(root, "/").name == "argon2id-real-browser-harness.html"
        assert module.safe_candidate_path(root, "/goreevault_web_argon2id_core_bg.wasm").name.endswith(".wasm")
        expect_raises(FileNotFoundError, module.safe_candidate_path, root, "/../secret")
        expect_raises(FileNotFoundError, module.safe_candidate_path, root, "/not-allowed.js")
        target = root / "goreevault_web_argon2id_core.js"
        target.unlink()
        target.symlink_to(root / "argon2id-real-browser-harness.js")
        expect_raises(FileNotFoundError, module.safe_candidate_path, root, "/goreevault_web_argon2id_core.js")

    assert "default-src 'none'" in module.CSP
    assert "script-src 'self'" in module.CSP
    assert "connect-src 'self'" in module.CSP
    assert "frame-ancestors 'none'" in module.CSP
    print("Argon2id browser harness server safety tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
