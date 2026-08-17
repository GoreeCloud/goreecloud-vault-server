# Argon2id Provider Dependency Basis

GoreeVault pins the Argon2id core and its browser binding dependencies so the reviewed source and generated ABI remain reproducible.

- `argon2 = 0.6.0-rc.8` — RustCrypto Argon2 implementation matching the reviewed Bitwarden primitive baseline.
- `zeroize = 1.9.0` — explicit zeroization of Rust-owned ABI input buffers.
- `wasm-bindgen = 0.2.126` — exact browser/WebAssembly binding crate, used only on `wasm32`.

The corresponding `wasm-bindgen-cli` version is also pinned to `0.2.126` in CI. Generated glue is used for isolated interoperability validation and is not approved for the GoreeVault Web production release until a separate runtime-registration gate is satisfied.
