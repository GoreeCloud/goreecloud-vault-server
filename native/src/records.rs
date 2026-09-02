//! Owner-scoped opaque encrypted-record development store.
//!
//! This module deliberately does not encrypt, decrypt, inspect, index, or log
//! protected record contents. The caller supplies already-protected ciphertext.
//! The in-memory store exists only to establish owner isolation and opaque-data
//! handling for the native application boundary.

use std::collections::HashMap;
use std::fmt;

pub const MAX_IDENTIFIER_BYTES: usize = 512;
pub const MAX_CIPHERTEXT_BYTES: usize = 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum StoreError {
    InvalidOwner,
    InvalidRecordId,
    InvalidRevision,
    EmptyCiphertext,
    CiphertextTooLarge,
}

impl fmt::Display for StoreError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let message = match self {
            Self::InvalidOwner => "invalid owner identity",
            Self::InvalidRecordId => "invalid record identifier",
            Self::InvalidRevision => "invalid record revision",
            Self::EmptyCiphertext => "encrypted record payload is empty",
            Self::CiphertextTooLarge => "encrypted record payload exceeds the development limit",
        };
        formatter.write_str(message)
    }
}

impl std::error::Error for StoreError {}

#[derive(Clone, Eq, PartialEq)]
pub struct EncryptedRecord {
    record_id: String,
    ciphertext: Vec<u8>,
    revision: u64,
}

impl EncryptedRecord {
    #[must_use]
    pub fn record_id(&self) -> &str {
        &self.record_id
    }

    #[must_use]
    pub fn ciphertext(&self) -> &[u8] {
        &self.ciphertext
    }

    #[must_use]
    pub const fn revision(&self) -> u64 {
        self.revision
    }
}

impl fmt::Debug for EncryptedRecord {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EncryptedRecord")
            .field("record_id", &self.record_id)
            .field("ciphertext_len", &self.ciphertext.len())
            .field("revision", &self.revision)
            .finish()
    }
}

#[derive(Default)]
pub struct MemoryStore {
    records_by_owner: HashMap<String, HashMap<String, EncryptedRecord>>,
}

impl MemoryStore {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Store or replace one owner's encrypted record.
    ///
    /// # Errors
    ///
    /// Returns a bounded [`StoreError`] when the owner, record identifier,
    /// revision, or encrypted payload does not satisfy the development contract.
    pub fn put(
        &mut self,
        owner_id: &str,
        record_id: &str,
        ciphertext: Vec<u8>,
        revision: u64,
    ) -> Result<(), StoreError> {
        validate_owner(owner_id)?;
        validate_record_id(record_id)?;
        validate_ciphertext(&ciphertext)?;
        if revision == 0 {
            return Err(StoreError::InvalidRevision);
        }

        let record = EncryptedRecord {
            record_id: record_id.to_owned(),
            ciphertext,
            revision,
        };
        self.records_by_owner.entry(owner_id.to_owned()).or_default().insert(record_id.to_owned(), record);
        Ok(())
    }

    /// Return one record only inside the supplied owner boundary.
    ///
    /// # Errors
    ///
    /// Returns a bounded [`StoreError`] when the owner or record identifier is invalid.
    pub fn get(&self, owner_id: &str, record_id: &str) -> Result<Option<&EncryptedRecord>, StoreError> {
        validate_owner(owner_id)?;
        validate_record_id(record_id)?;
        Ok(self.records_by_owner.get(owner_id).and_then(|records| records.get(record_id)))
    }

    /// Return the supplied owner's records ordered by record identifier.
    ///
    /// # Errors
    ///
    /// Returns [`StoreError::InvalidOwner`] when the owner identifier is invalid.
    pub fn list(&self, owner_id: &str) -> Result<Vec<&EncryptedRecord>, StoreError> {
        validate_owner(owner_id)?;
        let mut records: Vec<&EncryptedRecord> =
            self.records_by_owner.get(owner_id).into_iter().flat_map(|records| records.values()).collect();
        records.sort_unstable_by(|left, right| left.record_id.cmp(&right.record_id));
        Ok(records)
    }

    /// Delete one record only inside the supplied owner boundary.
    ///
    /// # Errors
    ///
    /// Returns a bounded [`StoreError`] when the owner or record identifier is invalid.
    pub fn delete(&mut self, owner_id: &str, record_id: &str) -> Result<bool, StoreError> {
        validate_owner(owner_id)?;
        validate_record_id(record_id)?;

        let Some(records) = self.records_by_owner.get_mut(owner_id) else {
            return Ok(false);
        };
        let removed = records.remove(record_id).is_some();
        if records.is_empty() {
            self.records_by_owner.remove(owner_id);
        }
        Ok(removed)
    }
}

fn validate_owner(owner_id: &str) -> Result<(), StoreError> {
    if valid_identifier(owner_id) {
        Ok(())
    } else {
        Err(StoreError::InvalidOwner)
    }
}

fn validate_record_id(record_id: &str) -> Result<(), StoreError> {
    if valid_identifier(record_id) {
        Ok(())
    } else {
        Err(StoreError::InvalidRecordId)
    }
}

fn valid_identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= MAX_IDENTIFIER_BYTES
        && value.trim() == value
        && !value.chars().any(char::is_control)
}

fn validate_ciphertext(ciphertext: &[u8]) -> Result<(), StoreError> {
    if ciphertext.is_empty() {
        return Err(StoreError::EmptyCiphertext);
    }
    if ciphertext.len() > MAX_CIPHERTEXT_BYTES {
        return Err(StoreError::CiphertextTooLarge);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{MAX_CIPHERTEXT_BYTES, MAX_IDENTIFIER_BYTES, MemoryStore, StoreError};

    #[test]
    fn same_record_identifier_is_isolated_between_owners() {
        let mut store = MemoryStore::new();
        assert_eq!(store.put("owner-a", "record-1", b"ciphertext-a".to_vec(), 1), Ok(()));
        assert_eq!(store.put("owner-b", "record-1", b"ciphertext-b".to_vec(), 1), Ok(()));

        assert_eq!(
            store.get("owner-a", "record-1").map(|record| record.map(|record| record.ciphertext())),
            Ok(Some(&b"ciphertext-a"[..]))
        );
        assert_eq!(
            store.get("owner-b", "record-1").map(|record| record.map(|record| record.ciphertext())),
            Ok(Some(&b"ciphertext-b"[..]))
        );
    }

    #[test]
    fn cross_owner_lookup_does_not_return_another_owners_record() {
        let mut store = MemoryStore::new();
        assert_eq!(store.put("owner-a", "record-1", b"opaque-data".to_vec(), 1), Ok(()));

        assert_eq!(store.get("owner-b", "record-1"), Ok(None));
    }

    #[test]
    fn list_and_delete_remain_owner_scoped() {
        let mut store = MemoryStore::new();
        assert_eq!(store.put("owner-a", "record-b", b"ciphertext-b".to_vec(), 1), Ok(()));
        assert_eq!(store.put("owner-a", "record-a", b"ciphertext-a".to_vec(), 2), Ok(()));
        assert_eq!(store.put("owner-b", "record-c", b"ciphertext-c".to_vec(), 1), Ok(()));

        assert_eq!(
            store
                .list("owner-a")
                .map(|records| { records.into_iter().map(|record| record.record_id()).collect::<Vec<_>>() }),
            Ok(vec!["record-a", "record-b"])
        );

        assert_eq!(store.delete("owner-b", "record-a"), Ok(false));
        assert!(matches!(store.get("owner-a", "record-a"), Ok(Some(_))));
    }

    #[test]
    fn invalid_identifiers_fail_before_storage_access() {
        let store = MemoryStore::new();
        assert_eq!(store.get("", "record-1"), Err(StoreError::InvalidOwner));

        let oversized = "x".repeat(MAX_IDENTIFIER_BYTES + 1);
        assert_eq!(store.get("owner-a", &oversized), Err(StoreError::InvalidRecordId));
    }

    #[test]
    fn ciphertext_is_bounded_without_being_interpreted() {
        let mut store = MemoryStore::new();
        assert_eq!(store.put("owner-a", "record-1", Vec::new(), 1), Err(StoreError::EmptyCiphertext));
        assert_eq!(
            store.put("owner-a", "record-1", vec![0_u8; MAX_CIPHERTEXT_BYTES + 1], 1,),
            Err(StoreError::CiphertextTooLarge)
        );

        let arbitrary_bytes = vec![0, 255, 17, 42];
        assert_eq!(store.put("owner-a", "record-2", arbitrary_bytes.clone(), 1), Ok(()));
        assert_eq!(
            store.get("owner-a", "record-2").map(|record| record.map(|record| record.ciphertext().to_vec())),
            Ok(Some(arbitrary_bytes))
        );
    }

    #[test]
    fn debug_output_does_not_include_ciphertext_bytes() {
        let mut store = MemoryStore::new();
        assert_eq!(store.put("owner-a", "record-1", b"never-log-this".to_vec(), 1), Ok(()));

        let rendered = store.get("owner-a", "record-1").map(|record| record.map(|record| format!("{record:?}")));
        assert!(matches!(
            rendered,
            Ok(Some(text)) if text.contains("ciphertext_len") && !text.contains("never-log-this")
        ));
    }

    #[test]
    fn revision_zero_is_rejected() {
        let mut store = MemoryStore::new();
        assert_eq!(store.put("owner-a", "record-1", b"ciphertext".to_vec(), 0), Err(StoreError::InvalidRevision));
    }
}
