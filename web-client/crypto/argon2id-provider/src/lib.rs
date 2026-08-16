#![forbid(unsafe_code)]

//! `GoreeVault` Web's pre-alpha Argon2id provider core.
//!
//! This crate intentionally contains no JavaScript/WASM binding. It proves the
//! Bitwarden-compatible Argon2id primitive and its wasm32 buildability before a
//! separate browser ABI is approved.

use argon2::{Algorithm, Argon2, Params, Version};

/// Bitwarden-compatible Argon2id version 1.3.
pub const ARGON2ID_VERSION: u32 = 0x13;
/// Bitwarden-compatible derived key size.
pub const OUTPUT_BYTES: usize = 32;
/// Minimum accepted Argon2id iterations.
pub const MIN_ITERATIONS: u32 = 2;
/// Minimum accepted Argon2id memory in KiB (16 MiB).
pub const MIN_MEMORY_KIB: u32 = 16 * 1024;
/// Minimum accepted Argon2id parallelism.
pub const MIN_PARALLELISM: u32 = 1;

/// Errors produced by the narrowly scoped provider core.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProviderError {
    /// One or more KDF parameters are below the GoreeVault/Bitwarden minimum.
    InsufficientParameters,
    /// `RustCrypto` rejected the supplied parameter combination.
    InvalidParameters,
    /// Argon2id derivation failed.
    DerivationFailed,
}

/// Derive exactly 32 bytes using Bitwarden-compatible Argon2id semantics.
///
/// `salt_sha256` must already be the SHA-256 digest of the normalized account
/// identifier. The JavaScript boundary owns that normalization and hashing so
/// this low-level core cannot accidentally diverge from the account protocol.
///
/// # Errors
///
/// Returns [`ProviderError::InsufficientParameters`] when any supplied KDF
/// parameter is below the reviewed minimum, [`ProviderError::InvalidParameters`]
/// when `RustCrypto` rejects the parameter combination, or
/// [`ProviderError::DerivationFailed`] when Argon2id derivation fails.
pub fn derive_argon2id(
    secret: &[u8],
    salt_sha256: &[u8; OUTPUT_BYTES],
    iterations: u32,
    memory_kib: u32,
    parallelism: u32,
) -> Result<[u8; OUTPUT_BYTES], ProviderError> {
    if iterations < MIN_ITERATIONS || memory_kib < MIN_MEMORY_KIB || parallelism < MIN_PARALLELISM {
        return Err(ProviderError::InsufficientParameters);
    }

    let params = Params::new(memory_kib, iterations, parallelism, Some(OUTPUT_BYTES))
        .map_err(|_| ProviderError::InvalidParameters)?;
    let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
    let mut output = [0_u8; OUTPUT_BYTES];

    argon2.hash_password_into(secret, salt_sha256, &mut output).map_err(|_| ProviderError::DerivationFailed)?;

    clear_argon2_stack_residue();
    Ok(output)
}

/// Force overwrite of a stack region after Argon2id, mirroring Bitwarden's
/// current defensive cleanup for stack memory used by the implementation.
#[inline(never)]
fn clear_argon2_stack_residue() {
    std::hint::black_box([0_u8; 4096]);
}

#[cfg(test)]
mod tests {
    use super::*;

    const BITWARDEN_TEST_SALT_SHA256: [u8; OUTPUT_BYTES] = [
        146, 72, 142, 30, 62, 238, 205, 249, 159, 62, 210, 206, 89, 35, 62, 251, 75, 79, 182, 18, 213, 101, 92, 12,
        233, 234, 82, 181, 165, 2, 230, 85,
    ];

    const BITWARDEN_EXPECTED: [u8; OUTPUT_BYTES] = [
        207, 240, 225, 177, 162, 19, 163, 76, 98, 106, 179, 175, 224, 9, 17, 240, 20, 147, 237, 47, 246, 150, 141, 184,
        62, 225, 131, 242, 51, 53, 225, 242,
    ];

    #[test]
    fn bitwarden_argon2id_vector_matches() {
        let derived = derive_argon2id(b"67t9b5g67$%Dh89n", &BITWARDEN_TEST_SALT_SHA256, 4, 32 * 1024, 2);

        assert_eq!(derived, Ok(BITWARDEN_EXPECTED));
    }

    #[test]
    fn minimum_parameters_are_enforced() {
        assert_eq!(
            derive_argon2id(b"secret", &[0_u8; OUTPUT_BYTES], 1, 16 * 1024, 1),
            Err(ProviderError::InsufficientParameters)
        );
        assert_eq!(
            derive_argon2id(b"secret", &[0_u8; OUTPUT_BYTES], 2, 15 * 1024, 1),
            Err(ProviderError::InsufficientParameters)
        );
        assert_eq!(
            derive_argon2id(b"secret", &[0_u8; OUTPUT_BYTES], 2, 16 * 1024, 0),
            Err(ProviderError::InsufficientParameters)
        );
    }

    #[test]
    fn provider_contract_constants_match_reviewed_bitwarden_semantics() {
        assert_eq!(ARGON2ID_VERSION, 0x13);
        assert_eq!(OUTPUT_BYTES, 32);
        assert_eq!(MIN_ITERATIONS, 2);
        assert_eq!(MIN_MEMORY_KIB, 16 * 1024);
        assert_eq!(MIN_PARALLELISM, 1);
    }
}
